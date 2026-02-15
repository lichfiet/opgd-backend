#!/bin/bash
set -e

echo "🚀 Deploying OPGD Mail & Manifest API to Lambda"
echo ""

# Check if function name is provided
FUNCTION_NAME="${1:-opgd-mail-manifest-api-prod}"

echo "📦 Creating deployment package..."

# Create temporary package directory
rm -rf package deployment.zip
mkdir -p package

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -t package/ --quiet

# Copy application code
echo "📋 Copying application code..."
cp -r routes shared security entrypoint.py package/

# Create zip file
echo "🗜️  Creating zip archive..."
cd package
zip -r ../deployment.zip . -q
cd ..

# Get zip file size
SIZE=$(du -h deployment.zip | cut -f1)
echo "✅ Package created: deployment.zip ($SIZE)"

# Deploy to Lambda
echo ""
echo "☁️  Uploading to Lambda function: $FUNCTION_NAME"
aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://deployment.zip \
  --output json | jq -r '"✅ Deployed version: " + .Version + " (updated: " + .LastModified + ")"'

# Clean up
echo ""
echo "🧹 Cleaning up..."
rm -rf package

echo ""
echo "✨ Deployment complete!"
echo ""
echo "Test your API:"
echo "aws lambda invoke --function-name $FUNCTION_NAME --payload '{\"rawPath\":\"/health\",\"requestContext\":{\"http\":{\"method\":\"GET\"}}}' response.json && cat response.json"
