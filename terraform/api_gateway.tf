resource "aws_apigatewayv2_api" "api" {
  name          = "opgd-mail-manifest-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [
      "https://onpointgaragedoors.com",
      "https://www.onpointgaragedoors.com",
      "http://localhost:5173",
    ]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["*"]
    expose_headers = ["*"]
    max_age = 3600
    allow_credentials = true
  }

  tags = {
    Name        = "OPGD API Gateway"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.api.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.api.id
  name        = "$default"
  auto_deploy = true

  tags = {
    Name        = "OPGD API Stage"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}
