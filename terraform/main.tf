module "pykata_dynamodb_table" {
  source = "./modules/dynamodb"

  dynamodb_table_name        = var.dynamodb_table_name
  billing_mode               = var.billing_mode
  attribute_definitions      = var.attribute_definitions
  provisioned_read_capacity  = var.provisioned_read_capacity
  provisioned_write_capacity = var.provisioned_write_capacity
}

module "pykata_bucket" {
  source = "./modules/s3"

  bucket_name        = var.s3_bucket_name
  versioning_enabled = var.s3_versioning_enabled
  force_destroy      = var.s3_force_destroy
  acl                = var.s3_acl
  tags               = var.tags
}
