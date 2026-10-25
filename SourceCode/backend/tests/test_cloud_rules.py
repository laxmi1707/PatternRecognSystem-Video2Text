from __future__ import annotations

import pytest

from app.knowledge.sop_generator import SOPGenerator
from app.ml.cloud_rules import CLOUD_SERVICE_LABELS, OPERATION_LABELS, decide_cloud_label
from app.ml.dataset_loader import derive_activity_label
from app.services.classification_service import decide_segment_labels


# ── rules on task instructions ─────────────────────────────────────────────────

@pytest.mark.parametrize(("instruction", "service", "ops"), [
    ("Upload a file to an S3 bucket", "cloud_storage", ["upload"]),
    ("Terminate the EC2 instance", "cloud_compute", ["delete"]),
    ("Create a security group", "cloud_networking", ["create"]),
    ("Store a secret in Secrets Manager", "cloud_identity_security", ["create"]),
    ("Take a snapshot of the RDS database", "cloud_database", []),
    ("View the CloudWatch log group for the service", "cloud_monitoring", ["view"]),
])
def test_instruction_service_and_operation(instruction, service, ops):
    d = decide_cloud_label(instruction, source="instruction")
    assert d is not None and d.service == service
    assert d.operations == ops
    assert d.service in CLOUD_SERVICE_LABELS and set(d.operations) <= set(OPERATION_LABELS)


@pytest.mark.parametrize("instruction", [
    "Create a new database for the app",  # no AWS evidence
    "Mute the notification bot of general channel",
    "List files in the current directory.",
])
def test_non_aws_instructions_are_not_labelled(instruction):
    assert decide_cloud_label(instruction, source="instruction") is None


# ── rules on screen text (OCR) ─────────────────────────────────────────────────

def test_console_url_decides_with_high_confidence():
    d = decide_cloud_label("https://s3.console.aws.amazon.com/s3/buckets/demo Upload succeeded "
                           "Files and folders (1 Total, 2.0 KB)")
    assert (d.service, d.operations) == ("cloud_storage", ["upload"])
    assert d.confidence == pytest.approx(0.95)
    assert d.evidence == ["url:s3.console"]


def test_security_group_page_inside_ec2_console_is_networking():
    d = decide_cloud_label("ap-southeast-1.console.aws.amazon.com/ec2/home#SecurityGroups: "
                           "Successfully created security group sg-0abc")
    assert (d.service, d.operations) == ("cloud_networking", ["create"])


def test_ec2_sidebar_listing_security_groups_stays_compute():
    d = decide_cloud_label("EC2 Dashboard Instances AMIs Security Groups Load Balancers "
                           "Terminate instance? i-0abc Successfully terminated")
    assert (d.service, d.operations) == ("cloud_compute", ["delete"])


def test_always_visible_buttons_are_not_operations():
    d = decide_cloud_label("Amazon S3 Buckets Create bucket Delete Empty Upload")
    assert d.service == "cloud_storage"
    assert d.operations == []


def test_ordinary_web_page_is_not_aws():
    assert decide_cloud_label("Google Search Images Gmail bucket list ideas") is None
    assert decide_cloud_label("") is None


def test_several_operations_in_one_segment_are_all_reported_in_order():
    d = decide_cloud_label("Amazon S3 Upload succeeded ... Delete objects To confirm deletion, "
                           "type permanently delete Successfully deleted")
    assert d.operations == ["upload", "delete"]


# ── who decides each segment ───────────────────────────────────────────────────

SEGMENTS = [
    {"start_time": 0, "end_time": 5, "ocr_text": "user@host:~$ ls Desktop Documents"},
    {"start_time": 5, "end_time": 10, "ocr_text": "console.aws.amazon.com/s3/buckets Upload succeeded"},
    {"start_time": 10, "end_time": 15, "ocr_text": ""},
]
MODELS = {
    "svm": [{"label": "web_browsing", "confidence": 0.9}] * 3,
    "stacking": [{"label": "terminal_ops", "confidence": 0.6}] * 3,
}


def test_hybrid_uses_rules_for_aws_segments_and_models_elsewhere():
    d = decide_segment_labels(SEGMENTS, MODELS, "hybrid")
    assert [(x["label"], x["source"]) for x in d] == [
        ("terminal_ops", "stacking"),  # tier 3 beats tier 1 even at lower confidence
        ("cloud_storage", "ocr_rules"),
        ("terminal_ops", "stacking"),
    ]
    assert d[1]["operations"] == ["upload"]


def test_rules_only_labels_unknown_segments_other():
    d = decide_segment_labels(SEGMENTS, {}, "rules")
    assert [x["label"] for x in d] == ["other", "cloud_storage", "other"]


def test_training_labels_are_unchanged_by_the_rules():
    # Rules run only when a video is analysed; dataset labels still come from
    # derive_activity_label, so existing models need no retraining.
    assert derive_activity_label("Upload a file to an S3 bucket", "Chromium") == "web_browsing"


# ── SOP wording ─────────────────────────────────────────────────────────────────

def test_sop_step_names_aws_area_and_operations_per_segment():
    segs = [
        {"start_time": 0, "end_time": 5, "predicted_label": "cloud_storage", "confidence": 0.95,
         "operations": ["upload"]},
        {"start_time": 5, "end_time": 9, "predicted_label": "cloud_compute", "confidence": 0.85,
         "operations": []},
    ]
    sop = SOPGenerator().generate_from_segments("Clean up", "Chromium", segs, ["", ""])
    assert [s.title for s in sop.steps] == ["AWS storage: upload", "AWS compute"]
    assert sop.steps[0].description.endswith("Operation: upload.")
