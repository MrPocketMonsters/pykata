variable "project_name" {
  description = "Project name"
  type        = string
  default     = "pykata"
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "PyKata"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}



variable "environment" {
  description = "Environment: dev, or prod"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be dev or prod."
  }
}

variable "aws_access_key" {
  description = "AWS Access Key"
  type        = string
  default     = "test"
}

variable "aws_secret_key" {
  description = "AWS Secret Key"
  type        = string
  default     = "test"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL (dev only)"
  type        = string
  default     = "http://localhost:4566"
}

variable "localstack_s3_endpoint" {
  description = "LocalStack S3 endpoint URL (dev only)"
  type        = string
  default     = "http://s3.localhost.localstack.cloud:4566"
}



variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 10
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "kata"
}

variable "s3_bucket_name" {
  description = "S3 bucket name"
  type        = string
  default     = "kata-code"
}
