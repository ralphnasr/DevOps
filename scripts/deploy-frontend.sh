#!/usr/bin/env bash
set -euo pipefail

# ── ShopCloud Frontend Deployment ──
# Uploads static frontend to S3 and invalidates CloudFront cache
# Usage: ./scripts/deploy-frontend.sh

AWS_REGION="${AWS_REGION:-us-east-1}"

# Get bucket and distribution from Terraform outputs
S3_BUCKET=$(cd terraform && terraform output -raw s3_static_bucket 2>/dev/null || echo "")
CF_DIST_ID=$(cd terraform && terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")

if [[ -z "$S3_BUCKET" ]]; then
  echo "ERROR: Could not determine S3 bucket. Run 'terraform apply' first."
  exit 1
fi

echo "=== Frontend Deploy ==="
echo "Bucket:       ${S3_BUCKET}"
echo "Distribution: ${CF_DIST_ID}"
echo "========================"

# Update config.js with production values
CF_DOMAIN=$(cd terraform && terraform output -raw cloudfront_domain 2>/dev/null || echo "")
COGNITO_DOMAIN=$(cd terraform && terraform output -raw cognito_customer_domain 2>/dev/null || echo "")
COGNITO_CLIENT=$(cd terraform && terraform output -raw cognito_customer_client_id 2>/dev/null || echo "")

if [[ -n "$CF_DOMAIN" ]]; then
  echo "Updating config.js with production values..."
  sed -i.bak \
    -e "s|http://localhost:8000|https://${CF_DOMAIN}|g" \
    -e "s|COGNITO_DOMAIN: \"\"|COGNITO_DOMAIN: \"${COGNITO_DOMAIN}\"|g" \
    -e "s|COGNITO_CLIENT_ID: \"\"|COGNITO_CLIENT_ID: \"${COGNITO_CLIENT}\"|g" \
    -e "s|http://localhost:3000/callback.html|https://${CF_DOMAIN}/callback.html|g" \
    frontend/js/config.js
fi

# Sync to S3
echo "Uploading to S3..."
aws s3 sync frontend/ "s3://${S3_BUCKET}/" \
  --delete \
  --cache-control "max-age=86400" \
  --exclude "*.bak"

# Set no-cache on config.js (it has env-specific values)
aws s3 cp "frontend/js/config.js" "s3://${S3_BUCKET}/js/config.js" \
  --cache-control "no-cache, no-store"

# Restore original config.js
if [[ -f frontend/js/config.js.bak ]]; then
  mv frontend/js/config.js.bak frontend/js/config.js
fi

# Invalidate CloudFront
if [[ -n "$CF_DIST_ID" ]]; then
  echo "Invalidating CloudFront cache..."
  aws cloudfront create-invalidation \
    --distribution-id "$CF_DIST_ID" \
    --paths "/*" \
    --no-cli-pager
fi

echo ""
echo "=== Frontend deployed ==="
echo "URL: https://${CF_DOMAIN:-$S3_BUCKET.s3.amazonaws.com}"
