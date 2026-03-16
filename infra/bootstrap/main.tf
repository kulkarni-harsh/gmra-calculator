# Bootstrap — run this ONCE before the main infra.
# Creates the S3 bucket used to store Terraform state.
# Uses local state itself (it's just one bucket — safe to recreate if lost).

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "local" {}
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "app_name" {
  type    = string
  default = "gmra-calculator"
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "tfstate" {
  # Bucket names are globally unique — embed account ID to avoid collisions
  bucket = "${var.app_name}-tfstate-${data.aws_caller_identity.current.account_id}"

  tags = { Name = "${var.app_name}-tfstate" }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"  # lets you roll back to a previous state file
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "state_bucket" {
  value       = aws_s3_bucket.tfstate.bucket
  description = "Copy this into infra/backend.hcl as the bucket name"
}
