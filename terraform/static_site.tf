# ---------------------------------------------------------------------------
# Static site hosting for opgd-web (replaces Amplify).
# ---------------------------------------------------------------------------
# Private S3 bucket + CloudFront (OAC) + ACM cert + Route53 alias.
#
# INTERIM DOMAIN: opgd.trevorlichfield.com — the onpointgaragedoors.com domain
# isn't accessible yet (registrar). When it is: create/import its hosted zone,
# then change var.site_domain / var.site_zone_name and apply. The cert, DNS
# validation, and alias records all key off those two variables.
#
# Apply order: shared-infra first (it owns the WAF + OIDC provider this file
# looks up), then this.

variable "site_domain" {
  description = "FQDN the site is served from"
  type        = string
  default     = "opgd.trevorlichfield.com"
}

variable "site_zone_name" {
  description = "Route53 hosted zone the site domain lives in (must already exist)"
  type        = string
  default     = "trevorlichfield.com"
}

variable "shared_waf_name" {
  description = "Name of the shared CloudFront Web ACL (from shared-infra)"
  type        = string
  default     = "shared-cloudfront-waf"
}

# --- Lookups (require shared-infra + the hosted zone to exist) ---------------

data "aws_route53_zone" "site" {
  name         = var.site_zone_name
  private_zone = false
}

# CLOUDFRONT-scoped Web ACLs can only be queried via us-east-1.
data "aws_wafv2_web_acl" "shared" {
  provider = aws.us_east_1
  name     = var.shared_waf_name
  scope    = "CLOUDFRONT"
}

# --- TLS certificate (must be us-east-1 for CloudFront) ----------------------
# DNS-validated so it auto-renews. The expired trevorlichfield.com certs in the
# account are intentionally NOT imported — expired/imported certs don't renew.

resource "aws_acm_certificate" "site" {
  provider          = aws.us_east_1
  domain_name       = var.site_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name        = "OPGD Web Site Certificate"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

resource "aws_route53_record" "site_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.site.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id         = data.aws_route53_zone.site.zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "site" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.site.arn
  validation_record_fqdns = [for r in aws_route53_record.site_cert_validation : r.fqdn]
}

# --- S3 bucket (private; CloudFront-only access via OAC) ---------------------

resource "aws_s3_bucket" "site" {
  bucket = "opgd-web-site-${var.environment}"

  tags = {
    Name        = "OPGD Web Site"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Fully private — unlike the images bucket, nothing reads this except CloudFront.
resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAC"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.site.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.site.arn
          }
        }
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.site]
}

# --- CloudFront ---------------------------------------------------------------

resource "aws_cloudfront_origin_access_control" "site" {
  name                              = "opgd-web-site-${var.environment}"
  description                       = "OAC for OPGD web site bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "site" {
  enabled             = true
  comment             = "OPGD Web Site"
  default_root_object = "index.html"
  aliases             = [var.site_domain]
  price_class         = "PriceClass_100" # NA + EU only; cheapest
  web_acl_id          = data.aws_wafv2_web_acl.shared.arn

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = "S3-site"
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  default_cache_behavior {
    target_origin_id       = "S3-site"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    # AWS managed "CachingOptimized" policy
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6"
  }

  # SPA routing: client-side routes (e.g. /services, /admin) are not S3 objects.
  # Serve index.html for them and let React Router take over.
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.site.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name        = "OPGD Web Site Distribution"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

# --- DNS ----------------------------------------------------------------------

resource "aws_route53_record" "site_a" {
  zone_id = data.aws_route53_zone.site.zone_id
  name    = var.site_domain
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "site_aaaa" {
  zone_id = data.aws_route53_zone.site.zone_id
  name    = var.site_domain
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }
}

# --- Outputs ------------------------------------------------------------------

output "site_url" {
  description = "Public URL of the static site"
  value       = "https://${var.site_domain}"
}

output "site_bucket_name" {
  description = "S3 bucket the CI workflow syncs the build into"
  value       = aws_s3_bucket.site.bucket
}

output "site_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation in CI)"
  value       = aws_cloudfront_distribution.site.id
}

output "site_cloudfront_domain" {
  description = "Raw CloudFront domain (useful for testing before DNS cutover)"
  value       = aws_cloudfront_distribution.site.domain_name
}
