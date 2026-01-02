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
}

resource "aws_lambda_function" "pykata_lambda" {
  function_name    = var.lambda_function_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "src.lambdas.health.handler"
  runtime          = "python3.12"
  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")
  timeout          = var.lambda_timeout
  memory_size      = 512

  environment {
    variables = {
      APP_NAME  = var.project_name,
      APP_ENV   = var.provider_environment,
      LOG_LEVEL = "INFO",
      DEBUG     = false,

      AWS_ACCESS_KEY_ID     = var.provider_aws_access_key,
      AWS_SECRET_ACCESS_KEY = var.provider_aws_secret_key,
      AWS_DEFAULT_REGION    = var.provider_aws_region,
      AWS_ENDPOINT          = var.lambda_env_aws_endpoint,
      AWS_S3_ENDPOINT       = var.lambda_env_aws_s3_endpoint,
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name,
      S3_BUCKET_NAME        = var.s3_bucket_name,

      LAMBDA_TIMEOUT    = var.lambda_timeout,
      EXECUTION_TIMEOUT = 300
    }
  }

  depends_on = [aws_iam_role.lambda_role]
}
