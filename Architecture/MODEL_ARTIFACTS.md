# Model Artifacts — S3 Storage and Startup Sync

How trained classifier artifacts are stored in AWS and loaded by the backend. Snapshot as of 2026-10-08;
re-check the code and `aws s3 ls` before relying on specifics.

## Summary

- Trained models live in a **private S3 bucket**, versioned by key prefix (`models/v1/`, `models/v2/`, ...).
- At startup the backend **downloads models from S3 into the local model directory**, then loads them as before.
- **Fallback:** if S3 is not configured or anything fails, the backend uses whatever is already in the local
  model directory (`./models`, which the Dockerfile bakes into the image via `COPY models ./models`).

## AWS resources

| Item | Value |
|------|-------|
| Account / region | `984263476980` / `ap-southeast-1` |
| Bucket | `video2knowledge-dev-model-artifacts-984263476980` |
| Terraform | `infra/aws/model-artifacts/` (separate root from `infra/aws/main.tf`, so applying it never touches the EC2 training stack) |
| State | **Local only**: `infra/aws/model-artifacts/terraform.tfstate` (gitignored). Don't delete it, and don't apply from another clone. |

Bucket hardening (verified with `aws s3api`): all four Block Public Access flags on, `PolicyStatus.IsPublic=false`,
ACLs disabled (`BucketOwnerEnforced`), SSE-S3 (AES256) by default, versioning enabled, a bucket policy that
denies non-TLS requests, a lifecycle rule that expires noncurrent versions after 90 days and aborts multipart
uploads after 7. Anonymous `GET` returns 403.

Terraform variables (`variables.tf`; copy `terraform.tfvars.example` to `terraform.tfvars`): `aws_region`, `aws_profile`,
`project_name`, `environment`, `bucket_name` (override; default `<project>-<env>-model-artifacts-<account_id>`),
`models_prefix`, `noncurrent_version_retention_days`, `force_destroy`, `create_read_policy`.

**IAM read policy is not created.** The deploying user (`ClaudeIAMRootUser`) lacks `iam:CreatePolicy`, so
`create_read_policy = false`. The policy JSON (`s3:ListBucket` on the prefix, plus `s3:GetObject`/`GetObjectVersion`
on `<prefix>/*`) is available via `terraform output models_read_policy_json`. An IAM admin must create it and
attach it to the backend runtime role (App Runner instance role, per `.github/workflows/deploy-backend.yml`).

## Bucket layout and uploaded versions

```
s3://video2knowledge-dev-model-artifacts-984263476980/
└── models/
    └── v1/                       # uploaded 2026-10-08 from SourceCode/backend/models/
        ├── <model_name>.pkl      # written by the classifier's own save(); name = registry name
        └── <model_name>.sha256   # hex SHA-256 of the .pkl
```

`v1` contains **Tier 1 only**: `decision_tree`, `knn`, `lightgbm`, `naive_bayes`, `random_forest`, `svm`, `xgboost`.
Tier 2 (`mlp`, `cnn1d`, `lstm`, `transformer`) and Tier 3 (`voting`, `stacking`, `late_fusion`) artifacts don't exist yet.

Publishing a new version: upload `.pkl` + `.sha256` to `models/vN/`, then point `MODEL_S3_PREFIX` at it.
Rollback: set the prefix back. Don't overwrite an existing version prefix.

```bash
B=video2knowledge-dev-model-artifacts-984263476980
for f in models/*.pkl; do sha256sum "$f" | awk '{print $1}' > "${f%.pkl}.sha256"; done
aws s3 cp models/ s3://$B/models/v2/ --recursive --exclude "*" --include "*.pkl" --include "*.sha256"
```

## Backend startup sync

Code: `SourceCode/backend/app/ml/model_sync.py::sync_models_from_s3`, called from
`MLService.__init__` → `_sync_models_from_s3()` **before** `_try_load_models()` (`app/services/ml_service.py`).
`ml_service` is a module-level singleton, so the sync runs on first import (API startup, and also `train.py`).

Settings (`app/config.py`, env vars; see `SourceCode/backend/.env.example`):

| Env var | Default | Meaning |
|---------|---------|---------|
| `MODEL_S3_BUCKET` | `video2knowledge-dev-model-artifacts-984263476980` | Empty (`MODEL_S3_BUCKET=`) → skip S3, local models only |
| `MODEL_S3_PREFIX` | `models/v1` | Version prefix |
| `MODEL_S3_REGION` | `ap-southeast-1` | boto3 region |
| `MODEL_S3_REQUIRE_CHECKSUM` | `false` | `true` → skip any model without a `.sha256` |

Behaviour:

- Downloads only `*.pkl` directly under the prefix; nested prefixes (other versions) are ignored.
- S3 files overwrite local files of the same name. Models missing from S3 keep their local copy.
- Each file downloads to a `.part` temp file and is `os.replace`d into place, so a failed or corrupt download
  never clobbers the local fallback.
- If `<name>.sha256` exists, it is verified; a mismatch keeps the local copy.
- Any failure (no bucket, `boto3` missing, no credentials, network, `NoSuchBucket`, empty prefix) logs a warning
  and falls back to local. **It never raises**, so startup is never blocked by S3.
- `boto3` is the optional extra `aws` in `pyproject.toml`; the Dockerfile installs `.[ml,aws]`.

Tests: `SourceCode/backend/tests/ml/test_model_sync.py` (fake S3 client; covers no bucket, download, list failure,
per-file download failure, empty prefix, nested prefixes, checksum match/mismatch, required checksum).
Also verified against the real bucket: `models/v1` downloads 7/7 with checksums required, byte-identical to local.

## Still open

1. **Deployed backend needs read access:** the bucket/prefix/region are now code defaults, so no env vars are
   required on App Runner, but the App Runner instance role still needs the IAM read policy. Until then the
   sync logs `AccessDenied` and the service falls back to the models baked into the image.
   Local dev with AWS credentials will also overwrite `./models/*.pkl` with `models/v1` at startup; set
   `MODEL_S3_BUCKET=` in `.env` to keep locally trained models.
2. **Missing models are trained silently:** `MLService.classify()` → `_ensure_trained()` fits any model without
   a loaded artifact during the request, on real data or a synthetic fallback. Video analysis runs all 14 models
   (`classification_service.ALL_MODELS`), so the 7 Tier 2/3 models are trained on the fly in deployment.
3. **Label names are positional:** `classify()` maps output indices to the hard-coded `ACTIVITY_LABELS` in
   `app/ml/config.py` (legacy DevOps labels), not to the model's own `classes_`.
4. **Classifiers save and load with raw `pickle`/`torch.load`.** `app/ml/safe_model_io.py` exists but isn't used.
   Integrity checking happens only in the S3 sync. Only load artifacts from this private bucket.
