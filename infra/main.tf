terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # S3 backend — bucket is created by infra/bootstrap first.
  # Init with: terraform init -backend-config=backend.hcl
  backend "s3" {
    bucket = "gmra-calculator-tfstate-707057771327"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}
