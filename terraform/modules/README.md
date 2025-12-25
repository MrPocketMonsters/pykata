# Terraform Modules Directory

This directory contains reusable Terraform modules used by the PyKata infrastructure. Each module is self-contained with its own `main.tf`, `variables.tf`, and `outputs.tf`.

Current modules:

- `dynamodb/` — DynamoDB table with a fixed partition key (`id`) and optional index attribute definitions.
- `s3/` — S3 bucket with optional versioning and canned ACL.

Planned modules:

- `lambda/` — AWS Lambda function with configurable runtime, handler, and environment variables.
- `api_gateway/` — API Gateway REST API with configurable resources and methods.
- `iam/` — IAM roles and policies for Lambda functions and other services.

---

## Module: DynamoDB (modules/dynamodb)

Purpose:

- Creates a DynamoDB table with a fixed partition key (`id`).
- Optionally declares additional attributes (used for index keys) and handles capacity when `billing_mode` is `PROVISIONED`.

Resources:

- `aws_dynamodb_table.this`

Variables:

- `dynamodb_table_name` (string): Name of the DynamoDB table.
- `billing_mode` (string): Billing mode for the table `(PAY_PER_REQUEST|PROVISIONED)`.
- `provisioned_read_capacity` (number): Read capacity units used when `billing_mode` is `PROVISIONED`.
- `provisioned_write_capacity` (number): Write capacity units used when `billing_mode` is `PROVISIONED`.
- `attribute_definitions` (list(object)): Additional attribute definitions (name, type `(S|N|B)`) intended for index keys. DynamoDB is schemaless; non-key item attributes do not need to be declared.

Outputs:

- `dynamodb_table_name`: Name of the created DynamoDB table.
- `dynamodb_table_arn`: ARN of the created DynamoDB table.

Example:

```hcl
module "pykata_dynamodb_table" {
  source = "modules/dynamodb"

  dynamodb_table_name        = var.dynamodb_table_name
  billing_mode               = var.billing_mode
  attribute_definitions      = var.attribute_definitions
  provisioned_read_capacity  = var.provisioned_read_capacity
  provisioned_write_capacity = var.provisioned_write_capacity
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.pykata_dynamodb_table.dynamodb_table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.pykata_dynamodb_table.dynamodb_table_arn
}
```

Notes:

- The module always defines `id` (type `S`) as the table hash key.
- To add GSIs/LSIs, define their key attributes in `attribute_definitions` and extend the table with `global_secondary_index` or `local_secondary_index` blocks.

---

## Module: S3 (modules/s3)

Purpose:

- Creates an S3 bucket with optional object versioning and a canned ACL.

Resources:

- `aws_s3_bucket.this`
- `aws_s3_bucket_versioning.this`
- `aws_s3_bucket_acl.this`

Variables:

- `bucket_name` (string): Name of the S3 bucket.
- `versioning_enabled` (bool): Enable object versioning (`true`|`false`). Default: `false`.
- `force_destroy` (bool): Force destroy even if objects exist. Default: `false`.
- `acl` (string): Canned ACL for the bucket (e.g., `private`, `public-read`). Default: `private`.
- `tags` (map(string)): Tags to apply to the bucket. Default: `{}`.

Outputs:

- `bucket_name`: Name of the S3 bucket.
- `bucket_arn`: ARN of the S3 bucket.

Example:

```hcl
module "pykata_bucket" {
  source              = "modules/s3"
  bucket_name         = var.s3_bucket_name
  versioning_enabled  = true
  force_destroy       = false
  acl                 = "private"
  tags                = var.tags
}

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.pykata_bucket.bucket_name
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.pykata_bucket.bucket_arn
}
```

Notes:

- When using LocalStack (dev), ensure the provider is configured with appropriate endpoints and `s3_use_path_style = true` as needed.
