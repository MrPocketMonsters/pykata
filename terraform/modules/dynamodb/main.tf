resource "aws_dynamodb_table" "this" {
  name         = var.dynamodb_table_name
  billing_mode = var.billing_mode

  # Hash key
  hash_key = "id"
  attribute {
    name = "id"
    type = "S"
  }

  # Additional attributes
  dynamic "attribute" {
    for_each = var.attribute_definitions
    content {
      name = attribute.value.name
      type = attribute.value.type
    }
  }

  # Provisioned throughput (only if PROVISIONED billing mode)
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.provisioned_read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.provisioned_write_capacity : null
}
