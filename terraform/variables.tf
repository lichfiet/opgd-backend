variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-west-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "admin_password" {
  description = "Admin password for API authentication"
  type        = string
  sensitive   = true
}

variable "ses_sender_email" {
  description = "SES sender email address"
  type        = string
  default     = "noreply@onpointgaragedoors.com"
}

variable "ses_recipient_email" {
  description = "Business email to receive contact submissions"
  type        = string
  default     = "info@onpointgaragedoors.com"
}
