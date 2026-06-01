resource "aws_cloudfront_distribution" "main" {
  enabled = true
  comment = "OPGD Mail & Manifest API Distribution"

  # S3 Origin for images
  origin {
    domain_name = aws_s3_bucket.images_content.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.images_content.bucket}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.s3_oai.cloudfront_access_identity_path
    }
  }

  # API Gateway Origin
  origin {
    domain_name = replace(replace(aws_api_gateway_stage.api.invoke_url, "https://", ""), "/${var.environment}", "")
    origin_id   = "APIGateway"
    origin_path = "/${var.environment}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "APIGateway"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    compress               = true

    forwarded_values {
      query_string = true
      # Matches the live distribution (headers were added in the console to fix
      # CORS: FastAPI needs Origin/Access-Control-* forwarded to answer preflight).
      headers = [
        "Authorization",
        "Origin",
        "Accept",
        "Access-Control-Request-Method",
        "Access-Control-Allow-Origin",
        "Access-Control-Request-Headers",
        "Accept-Encoding",
        "Content-Type",
      ]

      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # Cache behavior for S3 images
  ordered_cache_behavior {
    path_pattern           = "/images/*"
    target_origin_id       = "S3-${aws_s3_bucket.images_content.bucket}"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    compress               = true

    forwarded_values {
      query_string = false

      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 86400
    max_ttl     = 31536000
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name        = "OPGD CloudFront Distribution"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}
