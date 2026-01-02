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

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/lambda/pykata_lambda_log_group"
  retention_in_days = 14
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
      "s3:GetObject",
      "dynamodb:PutItem",
      "dynamodb:GetItem",
    ]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda_iam_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  depends_on = [aws_cloudwatch_log_group.lambda_log_group]
}
