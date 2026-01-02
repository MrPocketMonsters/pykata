variable "project_name" {
  description = "Project name."
  type        = string
  default     = "pykata"
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}



variable "provider_environment" {
  description = "Deployment environment (e.g., dev, staging, prod)."
  type        = string
}

variable "provider_aws_endpoint" {
  description = "Endpoint where to send AWS API requests (passed from environment module)."
  type        = string
}

variable "provider_aws_s3_endpoint" {
  description = "Endpoint where to send AWS S3 API requests (passed from environment module)."
  type        = string
}
variable "provider_aws_access_key" {
  description = "AWS Access Key ID passed from environment module."
  type        = string
  sensitive   = true
}

variable "provider_aws_secret_key" {
  description = "AWS Secret Access Key passed from environment module."
  type        = string
  sensitive   = true
}

variable "provider_aws_region" {
  description = "AWS region passed from environment module."
  type        = string
}

variable "provider_s3_use_path_style" {
  description = "Use path-style S3 requests (passed from environment module)."
  type        = bool
  default     = false
}

variable "provider_skip_credentials_validation" {
  description = "Skip AWS credentials validation (passed from environment module)."
  type        = bool
  default     = false
}

variable "provider_skip_metadata_api_check" {
  description = "Skip metadata API check (passed from environment module)."
  type        = bool
  default     = false
}

variable "provider_skip_requesting_account_id" {
  description = "Skip requesting account ID (passed from environment module)."
  type        = bool
  default     = false
}

variable "dynamodb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "kata"
}

variable "billing_mode" {
  description = "Billing mode for the DynamoDB table (PAY_PER_REQUEST|PROVISIONED)"
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
  description = "Read capacity units used when billing_mode is PROVISIONED."
  type        = number
  default     = 5
}

variable "provisioned_write_capacity" {
  description = "Write capacity units used when billing_mode is PROVISIONED."
  type        = number
  default     = 5
}



variable "s3_bucket_name" {
  description = "S3 bucket name"
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
  default     = false
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



variable "lambda_timeout" {
  description = "Lambda function timeout in seconds."
  type        = number
  default     = 10
}

variable "lambda_function_name" {
  description = "Name of the Lambda function."
  type        = string
  default     = "pykata_lambda_function"
}

variable "lambda_env_aws_endpoint" {
  description = "Endpoint for AWS API requests inside Lambda (passed from environment module)."
  type        = string
}

variable "lambda_env_aws_s3_endpoint" {
  description = "Endpoint for AWS S3 API requests inside Lambda (passed from environment module)."
  type        = string
}
