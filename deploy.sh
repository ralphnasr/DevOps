#!/usr/bin/env bash
set -euo pipefail

# ══════════════════════════════════════════════════════════════
# ShopCloud — Single-Command Deploy (clean AWS account)
# Per docs/phase2-master-plan.md §14
# Usage: ./deploy.sh [dev|prod]   (default: prod)
# ══════════════════════════════════════════════════════════════

ENVIRONMENT="${1:-prod}"
AWS_REGION="${AWS_REGION:-us-east-1}"

if [[ "$ENVIRONMENT" != "dev" && "$ENVIRONMENT" != "prod" ]]; then
  echo "ERROR: environment must be 'dev' or 'prod' (got '${ENVIRONMENT}')"
  exit 1
fi

echo "════════════════════════════════════════════════"
echo " ShopCloud Deploy — ${ENVIRONMENT} (${AWS_REGION})"
echo "════════════════════════════════════════════════"

# ── 1. Prerequisite checks ──
echo "[1/5] Checking prerequisites..."
for tool in aws terraform docker; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "ERROR: '${tool}' not found in PATH"
    exit 1
  fi
done

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  echo "ERROR: AWS credentials not configured (run 'aws configure' or set AWS_PROFILE)"
  exit 1
fi

if [[ ! -f terraform/terraform.tfvars ]]; then
  echo "ERROR: terraform/terraform.tfvars not found"
  echo "  Copy terraform.tfvars.example to terraform.tfvars and fill in your values."
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "  Account: ${ACCOUNT_ID}"
echo "  Region:  ${AWS_REGION}"

# ── 2. Terraform apply — phase 1 (localhost-only Cognito callbacks) ──
echo "[2/6] Phase 1 apply: provisioning infrastructure..."
pushd terraform >/dev/null
terraform init -input=false
terraform apply -auto-approve -input=false

# ── 3. Terraform apply — phase 2 (real CloudFront domain into Cognito) ──
echo "[3/6] Phase 2 apply: wiring real CloudFront domain into Cognito..."
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain)
echo "  CloudFront domain: ${CLOUDFRONT_DOMAIN}"
terraform apply -auto-approve -input=false \
  -var="customer_callback_urls=[\"https://${CLOUDFRONT_DOMAIN}/callback.html\",\"http://localhost:3000/callback.html\"]" \
  -var="customer_logout_urls=[\"https://${CLOUDFRONT_DOMAIN}/index.html\",\"http://localhost:3000/index.html\"]"
popd >/dev/null

# ── 4. Build & push images, run migrations, update services ──
echo "[4/6] Building containers and deploying services..."
bash scripts/deploy.sh "$ENVIRONMENT"

# ── 5. Frontend ──
echo "[5/6] Deploying frontend to S3 + CloudFront..."
bash scripts/deploy-frontend.sh

# ── 6. Print connection info ──
echo "[6/6] Deployment complete. Endpoints:"
pushd terraform >/dev/null
echo ""
echo "  CloudFront URL:   https://$(terraform output -raw cloudfront_domain 2>/dev/null || echo 'n/a')"
if [[ "$ENVIRONMENT" == "prod" ]]; then
  echo "  ALB DNS (public): $(terraform output -raw prod_alb_dns 2>/dev/null || echo 'n/a')"
  echo "  RDS endpoint:     $(terraform output -raw prod_rds_endpoint 2>/dev/null || echo 'n/a')"
  echo "  Bastion IP:       $(terraform output -raw prod_bastion_ip 2>/dev/null || echo 'n/a')"
else
  echo "  ALB DNS:          $(terraform output -raw dev_alb_dns 2>/dev/null || echo 'n/a')"
  echo "  RDS endpoint:     $(terraform output -raw dev_rds_endpoint 2>/dev/null || echo 'n/a')"
  echo "  Bastion IP:       $(terraform output -raw dev_bastion_ip 2>/dev/null || echo 'n/a')"
fi
echo "  Cognito Hosted UI: $(terraform output -raw cognito_customer_domain 2>/dev/null || echo 'n/a')"
echo ""
popd >/dev/null
echo "════════════════════════════════════════════════"
echo " Deploy finished. Verify with:"
echo "   curl -I https://\$(cd terraform && terraform output -raw cloudfront_domain)"
echo "════════════════════════════════════════════════"
