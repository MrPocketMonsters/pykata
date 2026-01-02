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
  access_key = var.provider_aws_access_key
  secret_key = var.provider_aws_secret_key
  region     = var.provider_aws_region

  s3_use_path_style           = var.provider_s3_use_path_style
  skip_credentials_validation = var.provider_skip_credentials_validation
  skip_metadata_api_check     = var.provider_skip_metadata_api_check
  skip_requesting_account_id  = var.provider_skip_requesting_account_id

  endpoints {
    s3         = var.provider_aws_s3_endpoint
    dynamodb   = var.provider_aws_endpoint
    lambda     = var.provider_aws_endpoint
    apigateway = var.provider_aws_endpoint
    iam        = var.provider_aws_endpoint
    sqs        = var.provider_aws_endpoint
    sns        = var.provider_aws_endpoint
    cloudwatch = var.provider_aws_endpoint
    logs       = var.provider_aws_endpoint
  }
}
