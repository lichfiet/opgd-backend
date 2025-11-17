# OPGD Infrastructure - Terraform

Terraform configuration for the On Point Garage Doors Mail & Manifest API infrastructure.

## Infrastructure Components

- **DynamoDB**: Image metadata storage
- **S3**: Image file storage
- **Lambda**: FastAPI application runtime
- **API Gateway**: HTTP API endpoint
- **CloudFront**: CDN with S3 and API Gateway origins
- **IAM**: Lambda execution roles and policies
- **CloudWatch**: Lambda logs (7-day retention)

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with credentials
- Existing SES domain identity configured

## Setup

1. Copy the example variables file:
```bash
cp terraform.tfvars.example terraform.tfvars
```

2. Edit `terraform.tfvars` with your values:
```hcl
aws_region          = "us-west-1"
environment         = "prod"
admin_password      = "your_secure_password"
ses_sender_email    = "noreply@onpointgaragedoors.com"
ses_recipient_email = "info@onpointgaragedoors.com"
```

3. Initialize Terraform:
```bash
terraform init
```

4. Review the plan:
```bash
terraform plan
```

5. Apply the configuration:
```bash
terraform apply
```

6. Deploy your API code:
```bash
cd ../mail-and-manifest-api
./deploy.sh
```

## Outputs

After deployment, Terraform will output:

- `cloudfront_domain` - CloudFront distribution domain
- `cloudfront_url` - Full CloudFront URL
- `api_gateway_url` - Direct API Gateway endpoint
- `s3_bucket_name` - S3 bucket name
- `dynamodb_table_name` - DynamoDB table name
- `lambda_function_name` - Lambda function name

## Usage

Access your API via CloudFront:
```bash
https://<cloudfront_domain>/health
```

Or directly via API Gateway:
```bash
<api_gateway_url>/health
```

## Deployment Workflow

1. **Infrastructure**: `terraform apply` creates AWS resources
2. **Code Deployment**: `../mail-and-manifest-api/deploy.sh` uploads your API code

Terraform does NOT deploy your code automatically - use the `deploy.sh` script for code updates.

## Cost Optimization

- DynamoDB: Pay-per-request billing
- S3: No versioning enabled
- Lambda: 512MB memory, 30s timeout
- CloudWatch: 7-day log retention
- CloudFront: Standard distribution

## Files

- `main.tf` - Provider configuration
- `variables.tf` - Input variables
- `outputs.tf` - Output values
- `dynamodb.tf` - DynamoDB table
- `s3.tf` - S3 bucket and policies
- `iam.tf` - IAM roles and policies
- `lambda.tf` - Lambda function
- `api_gateway.tf` - API Gateway configuration
- `cloudfront.tf` - CloudFront distribution
- `ses.tf` - SES configuration (placeholder)

## Clean Up

To destroy all resources:
```bash
terraform destroy
```
