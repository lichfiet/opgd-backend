resource "aws_s3_bucket" "images_content" {
  bucket = "opgd-images-content-${var.environment}"

  tags = {
    Name        = "OPGD Images Content"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "images_content" {
  bucket = aws_s3_bucket.images_content.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "images_content" {
  bucket = aws_s3_bucket.images_content.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# CloudFront Origin Access Identity
resource "aws_cloudfront_origin_access_identity" "s3_oai" {
  comment = "OAI for OPGD S3 bucket"
}

# S3 Bucket Policy for CloudFront and Public Access
resource "aws_s3_bucket_policy" "images_content" {
  bucket = aws_s3_bucket.images_content.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontOAI"
        Effect = "Allow"
        Principal = {
          AWS = aws_cloudfront_origin_access_identity.s3_oai.iam_arn
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.images_content.arn}/*"
      },
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.images_content.arn}/*"
      }
    ]
  })
}
