variable "bucket_name" {
  description = "Name of the S3 bucket."
  type        = string
}

variable "versioning_enabled" {
  description = "Enable object versioning for the bucket (true|false)."
  type        = bool
  default     = false
}

variable "force_destroy" {
  description = "Force destroy the bucket even if it contains objects (use with caution)."
  type        = bool
  default     = false
}

variable "acl" {
  description = "Canned ACL for the bucket (e.g., private, public-read)."
  type        = string
  default     = "private"

  validation {
    condition = contains([
      "private",
      "public-read",
      "public-read-write",
      "aws-exec-read",
      "authenticated-read",
      "bucket-owner-read",
      "bucket-owner-full-control",
      "log-delivery-write"
    ], var.acl)
    error_message = "acl must be one of the standard S3 canned ACLs."
  }
}

variable "tags" {
  description = "Tags to apply to the bucket."
  type        = map(string)
  default     = {}
}
