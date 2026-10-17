# Private S3 bucket for trained model artifacts (<models_prefix>/<version>/<model_name>.pkl).
# Kept separate from ../main.tf so applying it never touches the EC2 training stack.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  bucket_name = coalesce(
    var.bucket_name,
    "${var.project_name}-${var.environment}-model-artifacts-${data.aws_caller_identity.current.account_id}",
  )
}

resource "aws_s3_bucket" "models" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = {
    Name = local.bucket_name
  }
}

# Block every form of public access.
resource "aws_s3_bucket_public_access_block" "models" {
  bucket = aws_s3_bucket.models.id

  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

# Disable ACLs entirely; access is governed by IAM and the bucket policy only.
resource "aws_s3_bucket_ownership_controls" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Versioning lets a bad model upload be rolled back.
resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "models" {
  bucket = aws_s3_bucket.models.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.models]
}

# Reject any request that is not over TLS.
data "aws_iam_policy_document" "bucket" {
  statement {
    sid     = "DenyInsecureTransport"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.models.arn,
      "${aws_s3_bucket.models.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }

  # Grant the backend's runtime role(s) read access from the bucket side, so no
  # IAM policy has to be created on the role (needs no iam:* permissions).
  dynamic "statement" {
    for_each = length(var.reader_role_arns) > 0 ? [1] : []
    content {
      sid       = "AllowReadersListModelsPrefix"
      effect    = "Allow"
      actions   = ["s3:ListBucket"]
      resources = [aws_s3_bucket.models.arn]

      principals {
        type        = "AWS"
        identifiers = var.reader_role_arns
      }

      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = ["${var.models_prefix}/*"]
      }
    }
  }

  dynamic "statement" {
    for_each = length(var.reader_role_arns) > 0 ? [1] : []
    content {
      sid       = "AllowReadersGetModelArtifacts"
      effect    = "Allow"
      actions   = ["s3:GetObject", "s3:GetObjectVersion"]
      resources = ["${aws_s3_bucket.models.arn}/${var.models_prefix}/*"]

      principals {
        type        = "AWS"
        identifiers = var.reader_role_arns
      }
    }
  }
}

resource "aws_s3_bucket_policy" "models" {
  bucket = aws_s3_bucket.models.id
  policy = data.aws_iam_policy_document.bucket.json

  depends_on = [aws_s3_bucket_public_access_block.models]
}

# Read-only access to the models prefix; attach to the backend's runtime role.
data "aws_iam_policy_document" "models_read" {
  statement {
    sid       = "ListModelsPrefix"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.models.arn]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["${var.models_prefix}/*"]
    }
  }

  statement {
    sid       = "ReadModelArtifacts"
    actions   = ["s3:GetObject", "s3:GetObjectVersion"]
    resources = ["${aws_s3_bucket.models.arn}/${var.models_prefix}/*"]
  }
}

resource "aws_iam_policy" "models_read" {
  count = var.create_read_policy ? 1 : 0

  name        = "${var.project_name}-${var.environment}-models-read"
  description = "Read-only access to ${local.bucket_name}/${var.models_prefix}/"
  policy      = data.aws_iam_policy_document.models_read.json
}
