output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.infra.dynamodb_table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.infra.dynamodb_table_arn
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.infra.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.infra.s3_bucket_arn
}

output "lambda_role_arn" {
  description = "ARN of the IAM Role for Lambda"
  value       = module.infra.lambda_role_arn
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.infra.lambda_function_arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.infra.lambda_function_name
}
