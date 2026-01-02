module "infra" {
  source = "../.."

  # Infrastructure configuration
  project_name               = var.project_name
  tags                       = var.tags
  lambda_timeout             = var.lambda_timeout
  dynamodb_table_name        = var.dynamodb_table_name
  billing_mode               = var.billing_mode
  attribute_definitions      = var.attribute_definitions
  provisioned_read_capacity  = var.provisioned_read_capacity
  provisioned_write_capacity = var.provisioned_write_capacity
  s3_bucket_name             = var.s3_bucket_name
  s3_versioning_enabled      = var.s3_versioning_enabled
  s3_force_destroy           = var.s3_force_destroy
  s3_acl                     = var.s3_acl

  # Provider configuration
  provider_aws_access_key              = var.aws_access_key
  provider_aws_secret_key              = var.aws_secret_key
  provider_aws_region                  = var.aws_region
  provider_s3_use_path_style           = var.s3_use_path_style
  provider_skip_credentials_validation = var.skip_credentials_validation
  provider_skip_metadata_api_check     = var.skip_metadata_api_check
  provider_skip_requesting_account_id  = var.skip_requesting_account_id
  provider_aws_s3_endpoint             = var.aws_s3_endpoint
  provider_aws_endpoint                = var.aws_endpoint
}
