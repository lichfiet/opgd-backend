terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

# The account is shared with other workloads; Project is the key Cost
# Explorer splits spend on, so it rides default_tags onto every resource.
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "opgd"
      Environment = var.environment
    }
  }
}

# us-east-1 alias — required for anything CloudFront consumes globally:
# ACM certificates and CLOUDFRONT-scoped WAF lookups must live/be queried there.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "opgd"
      Environment = var.environment
    }
  }
}
