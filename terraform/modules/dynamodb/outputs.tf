output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.this.name
}

output "dynamodb_table_arn" {
  description = "ARN or the DynamoDB table"
  value       = aws_dynamodb_table.this.arn
}
