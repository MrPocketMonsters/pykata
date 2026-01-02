output "region" {
  description = "AWS region used"
  value       = var.provider_aws_region
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "dynamodb_table_name" {
  description = "DynamoDB Table Name"
  value       = module.pykata_dynamodb_table.dynamodb_table_name
}

output "dynamodb_table_arn" {
  description = "DynamoDB Table ARN"
  value       = module.pykata_dynamodb_table.dynamodb_table_arn
}

output "s3_bucket_name" {
  description = "S3 Bucket Name"
  value       = module.pykata_bucket.bucket_name
}

output "s3_bucket_arn" {
  description = "S3 Bucket ARN"
  value       = module.pykata_bucket.bucket_arn
}

output "lambda_role_arn" {
  description = "IAM Role ARN for Lambda"
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_function_arn" {
  description = "Lambda Function ARN"
  value       = aws_lambda_function.pykata_lambda.arn
}
