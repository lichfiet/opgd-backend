resource "aws_dynamodb_table" "images_content" {
  name           = "opgd-images-content"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "uuid"

  attribute {
    name = "uuid"
    type = "S"
  }

  tags = {
    Name        = "OPGD Images Content"
    Environment = var.environment
    Project     = "On Point Garage Doors"
  }
}
