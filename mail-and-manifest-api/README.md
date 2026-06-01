# On Point Garage Doors - Mail & Manifest API

FastAPI-based REST API for managing image manifests and handling contact form submissions.

## API Endpoints

### Public Endpoints (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check endpoint |
| `GET` | `/images` | Get all images |
| `GET` | `/manifest` | Get images organized by category |
| `POST` | `/contact` | Submit contact form (sends email) |

### Admin Endpoints (Requires Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/image` | Upload new image to S3 + DynamoDB |
| `PUT` | `/image/{image_id}` | Update image metadata (description, tags) |
| `DELETE` | `/image/{image_id}` | Delete image from S3 + DynamoDB |

## Authentication

Admin endpoints require the `X-API-KEY` header, matching the `ADMIN_API_KEY`
environment variable:

```bash
X-API-KEY: <ADMIN_API_KEY>
```

Example:
```bash
curl -X POST http://localhost:8000/image \
  -H "X-API-KEY: your_secure_api_key" \
  -F "file=@image.jpg" \
  -F "description=A beautiful door" \
  -F "tags=doors"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DYNAMODB_TABLE_NAME` | DynamoDB table for image metadata | `opgd-images-content` |
| `S3_BUCKET_NAME` | S3 bucket for image storage | `opgd-images-content` |
| `SES_SENDER_EMAIL` | Email address for sending (must be verified in SES) | `noreply@onpointgaragedoors.com` |
| `SES_RECIPIENT_EMAIL` | Business email to receive contact submissions | `info@onpointgaragedoors.com` |
| `AWS_REGION` | AWS region for services | `us-west-1` |
| `ADMIN_API_KEY` | Key for admin authentication (sent as `X-API-KEY`) | _(none — required for admin endpoints)_ |
| `CLOUDFRONT_DOMAIN` | CloudFront domain for public image URLs (optional) | _(direct S3 URL)_ |
| `RECAPTCHA_SECRET_KEY` | reCAPTCHA v3 secret for `/contact` (optional) | _(disabled)_ |