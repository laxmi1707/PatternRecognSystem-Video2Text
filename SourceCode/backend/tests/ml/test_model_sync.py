import hashlib
import io

from app.ml.model_sync import sync_models_from_s3


class FakeS3:
    """Minimal stand-in for a boto3 S3 client backed by a dict of key -> bytes."""

    def __init__(self, objects: dict[str, bytes], fail_list: bool = False, fail_download: set[str] | None = None):
        self.objects = objects
        self.fail_list = fail_list
        self.fail_download = fail_download or set()

    def get_paginator(self, _name):
        fake = self

        class _Paginator:
            def paginate(self, Bucket, Prefix):
                if fake.fail_list:
                    raise RuntimeError("no credentials")
                yield {"Contents": [{"Key": k} for k in fake.objects if k.startswith(Prefix)]}

        return _Paginator()

    def download_file(self, bucket, key, filename):
        if key in self.fail_download:
            raise RuntimeError("network down")
        with open(filename, "wb") as f:
            f.write(self.objects[key])

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key])}


def _sha(data: bytes) -> bytes:
    return hashlib.sha256(data).hexdigest().encode()


def test_no_bucket_keeps_local(tmp_path):
    (tmp_path / "svm.pkl").write_bytes(b"local")
    assert sync_models_from_s3(None, "models", tmp_path) == []
    assert (tmp_path / "svm.pkl").read_bytes() == b"local"


def test_downloads_models_from_s3(tmp_path):
    s3 = FakeS3({"models/svm.pkl": b"remote-svm", "models/knn.pkl": b"remote-knn"})
    got = sync_models_from_s3("bucket", "models", tmp_path, client=s3)
    assert got == ["knn.pkl", "svm.pkl"]
    assert (tmp_path / "svm.pkl").read_bytes() == b"remote-svm"
    assert not list(tmp_path.glob("*.part"))


def test_s3_failure_falls_back_to_local(tmp_path):
    (tmp_path / "svm.pkl").write_bytes(b"local")
    s3 = FakeS3({"models/svm.pkl": b"remote"}, fail_list=True)
    assert sync_models_from_s3("bucket", "models", tmp_path, client=s3) == []
    assert (tmp_path / "svm.pkl").read_bytes() == b"local"


def test_failed_download_keeps_local_copy(tmp_path):
    (tmp_path / "svm.pkl").write_bytes(b"local")
    s3 = FakeS3({"models/svm.pkl": b"remote", "models/knn.pkl": b"remote-knn"}, fail_download={"models/svm.pkl"})
    assert sync_models_from_s3("bucket", "models", tmp_path, client=s3) == ["knn.pkl"]
    assert (tmp_path / "svm.pkl").read_bytes() == b"local"
    assert not list(tmp_path.glob("*.part"))


def test_empty_prefix_falls_back_to_local(tmp_path):
    s3 = FakeS3({"other/svm.pkl": b"remote"})
    assert sync_models_from_s3("bucket", "models", tmp_path, client=s3) == []


def test_ignores_nested_version_prefixes(tmp_path):
    s3 = FakeS3({"models/svm.pkl": b"top", "models/v2/svm.pkl": b"nested"})
    sync_models_from_s3("bucket", "models", tmp_path, client=s3)
    assert (tmp_path / "svm.pkl").read_bytes() == b"top"


def test_checksum_match_and_mismatch(tmp_path):
    (tmp_path / "knn.pkl").write_bytes(b"local-knn")
    s3 = FakeS3({
        "models/svm.pkl": b"remote-svm",
        "models/svm.sha256": _sha(b"remote-svm") + b"  svm.pkl\n",
        "models/knn.pkl": b"tampered",
        "models/knn.sha256": _sha(b"original"),
    })
    assert sync_models_from_s3("bucket", "models", tmp_path, client=s3) == ["svm.pkl"]
    assert (tmp_path / "knn.pkl").read_bytes() == b"local-knn"


def test_require_checksum_skips_unverified(tmp_path):
    s3 = FakeS3({"models/svm.pkl": b"remote"})
    assert sync_models_from_s3("bucket", "models", tmp_path, require_checksum=True, client=s3) == []
    assert not (tmp_path / "svm.pkl").exists()


def test_downloads_label_names_with_the_models_but_not_the_feature_cache(tmp_path):
    # label_names.json maps the models' class indices to names; X/y .npy are training data
    s3 = FakeS3({
        "models/svm.pkl": b"remote-svm",
        "models/label_names.json": b'["coding_editing"]',
        "models/X_train.npy": b"big",
    })
    got = sync_models_from_s3("bucket", "models", tmp_path, client=s3)
    assert got == ["label_names.json", "svm.pkl"]
    assert (tmp_path / "label_names.json").read_bytes() == b'["coding_editing"]'
    assert not (tmp_path / "X_train.npy").exists()
