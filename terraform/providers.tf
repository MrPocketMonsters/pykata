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
    s3         = lookup(var.provider_aws_endpoints, "s3", null)
    dynamodb   = lookup(var.provider_aws_endpoints, "dynamodb", null)
    lambda     = lookup(var.provider_aws_endpoints, "lambda", null)
    apigateway = lookup(var.provider_aws_endpoints, "apigateway", null)
  }
}
