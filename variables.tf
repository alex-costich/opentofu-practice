variable "project_name" {
  type        = string
  description = "Prefix for all AWS resources."
  default     = "support-ticket-classifier"
}

variable "aws_region" {
  type        = string
  description = "AWS region."
  default     = "us-east-1"
}

variable "bucket_name" {
  type        = string
  description = "S3 bucket where classified tickets land. Must be globally unique."
  default     = "support-ticket-classifier-tickets"
}
