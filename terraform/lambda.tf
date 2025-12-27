resource "aws_lambda_function" "api" {
  function_name = "opgd-mail-manifest-api-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "entrypoint.handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  # Dummy zip for initial creation - deploy code using deploy.sh script
  filename         = "${path.module}/lambda_placeholder.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda_placeholder.zip")

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.images_content.name
      S3_BUCKET_NAME      = aws_s3_bucket.images_content.bucket
      SES_SENDER_EMAIL    = var.ses_sender_email
      SES_RECIPIENT_EMAIL = var.ses_recipient_email
      ADMIN_PASSWORD      = var.admin_password
    }
  }

  tags = {
    env = var.environment
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 7

  tags = {
    Name        = "OPGD Lambda Logs"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}
