terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  access_key = var.aws_access_key
  secret_key = var.aws_secret_key
  region     = var.aws_region

  dynamic "s3_use_path_style" {
    for_each = var.environment == "dev" ? [1] : []
    content {
      s3_use_path_style = true
    }
  }

  # LocalStack configuration (dev only)
  dynamic "skip_credentials_validation" {
    for_each = var.environment == "dev" ? [1] : []
    content {
      skip_credentials_validation = true
    }
  }

  dynamic "skip_metadata_api_check" {
    for_each = var.environment == "dev" ? [1] : []
    content {
      skip_metadata_api_check = true
    }
  }

  dynamic "skip_requesting_account_id" {
    for_each = var.environment == "dev" ? [1] : []
    content {
      skip_requesting_account_id = true
    }
  }

  dynamic "endpoints" {
    for_each = var.environment == "dev" ? [1] : []
    content {
      s3         = var.localstack_s3_endpoint
      dynamodb   = var.localstack_endpoint
      lambda     = var.localstack_endpoint
      apigateway = var.localstack_endpoint
    }
  }
}
