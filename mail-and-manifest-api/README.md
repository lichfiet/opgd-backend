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
| `DELETE` | `/image/{image_id}` | Delete image from S3 + DynamoDB |
| `PUT` | `/manifest/{image_id}` | Update image metadata (tags, description) |
| `DELETE` | `/manifest/{image_id}` | Delete image from manifest |

## Authentication

Admin endpoints require a Bearer token in the `Authorization` header:

```bash
Authorization: Bearer <ADMIN_PASSWORD>
```

Example:
```bash
curl -X POST http://localhost:8000/image \
  -H "Authorization: Bearer your_secure_password" \
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
| `AWS_REGION` | AWS region for services | `us-east-1` |
| `ADMIN_PASSWORD` | Static password for admin authentication | `change_me_in_production` |