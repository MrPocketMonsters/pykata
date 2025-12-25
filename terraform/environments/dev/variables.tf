variable "project_name" {
  description = "Project name."
  type        = string
  default     = "pykata"
}

variable "tags" {
  description = "Common tags for all resources."
  type        = map(string)
  default = {
    Project     = "PyKata"
    ManagedBy   = "Terraform"
    Environment = "dev"
  }
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 10
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name."
  type        = string
  default     = "kata"
}

variable "billing_mode" {
  description = "Billing mode for the DynamoDB table (PAY_PER_REQUEST|PROVISIONED)."
  type        = string
  default     = "PAY_PER_REQUEST"

  validation {
    condition     = contains(["PAY_PER_REQUEST", "PROVISIONED"], var.billing_mode)
    error_message = "billing_mode must be PAY_PER_REQUEST or PROVISIONED."
  }
}

variable "attribute_definitions" {
  description = "List of attribute definitions for DynamoDB indexes (name, type S|N|B)."
  type = list(object({
    name = string
    type = string
  }))
  default = []

  validation {
    condition = length([
      for a in var.attribute_definitions : true
      if contains(["S", "N", "B"], a.type)
    ]) == length(var.attribute_definitions)
    error_message = "Each attribute type must be one of S, N, or B."
  }
}

variable "provisioned_read_capacity" {
  description = "Read capacity units when billing_mode is PROVISIONED."
  type        = number
  default     = 5
}

variable "provisioned_write_capacity" {
  description = "Write capacity units when billing_mode is PROVISIONED."
  type        = number
  default     = 5
}

variable "s3_bucket_name" {
  description = "S3 bucket name."
  type        = string
  default     = "kata-code"
}

variable "s3_versioning_enabled" {
  description = "Enable object versioning for the S3 bucket."
  type        = bool
  default     = false
}

variable "s3_force_destroy" {
  description = "Force destroy the S3 bucket even if it contains objects (use with caution)."
  type        = bool
  default     = true
}

variable "s3_acl" {
  description = "Canned ACL for the S3 bucket (e.g., private, public-read)."
  type        = string
  default     = "private"

  validation {
    condition = contains([
      "private",
      "public-read",
      "public-read-write",
      "authenticated-read",
      "log-delivery-write",
      "aws-exec-read",
      "bucket-owner-read",
      "bucket-owner-full-control"
    ], var.s3_acl)
    error_message = "s3_acl must be one of the standard S3 canned ACLs."
  }
}

# Provider/auth configuration (dev-specific)

variable "aws_access_key" {
  description = "AWS Access Key ID."
  type        = string
  default     = "test"
}

variable "aws_secret_key" {
  description = "AWS Secret Access Key."
  type        = string
  default     = "test"
}

variable "aws_region" {
  description = "AWS region."
  type        = string
  default     = "us-east-1"
}

variable "localstack_endpoint" {
  description = "LocalStack endpoint URL."
  type        = string
  default     = "http://localhost:4566"
}

variable "localstack_s3_endpoint" {
  description = "LocalStack S3 endpoint URL."
  type        = string
  default     = "http://s3.localhost.localstack.cloud:4566"
}

variable "s3_use_path_style" {
  description = "Use path-style S3 requests (enable for LocalStack)."
  type        = bool
  default     = true
}

variable "skip_credentials_validation" {
  description = "Skip AWS credentials validation (enable for LocalStack)."
  type        = bool
  default     = true
}

variable "skip_metadata_api_check" {
  description = "Skip metadata API check (enable for LocalStack)."
  type        = bool
  default     = true
}

variable "skip_requesting_account_id" {
  description = "Skip requesting account ID (enable for LocalStack)."
  type        = bool
  default     = true
}

variable "aws_endpoints" {
  description = "Custom service endpoints (e.g., for LocalStack)."
  type        = map(string)
  default = {
    s3         = "http://s3.localhost.localstack.cloud:4566"
    dynamodb   = "http://localhost:4566"
    lambda     = "http://localhost:4566"
    apigateway = "http://localhost:4566"
  }
}
