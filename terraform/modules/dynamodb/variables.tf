variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
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
  description = "List of attribute definitions for the DynamoDB table (other than the hash key); each attribute is an object with name and type (S|N|B)"

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
