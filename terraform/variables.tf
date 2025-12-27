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

variable "admin_api_key" {
  description = "Admin API key for authenticated endpoints"
  type        = string
  sensitive   = true
}

variable "cloudfront_domain" {
  description = "CloudFront distribution domain (optional, for image URLs)"
  type        = string
  default     = ""
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
