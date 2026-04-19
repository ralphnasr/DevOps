#!/usr/bin/env bash
set -euo pipefail

# ── ShopCloud Deployment Script ──
# Usage: ./scripts/deploy.sh <environment> [service]
# Examples:
#   ./scripts/deploy.sh dev          # Deploy all services to dev
#   ./scripts/deploy.sh prod catalog # Deploy only catalog to prod
#   ./scripts/deploy.sh prod         # Deploy all services to prod

ENVIRONMENT="${1:?Usage: deploy.sh <dev|prod> [service]}"
SERVICE="${2:-all}"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_BASE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
CLUSTER="shopcloud-${ENVIRONMENT}"

SERVICES=("catalog" "cart" "checkout" "admin")
if [[ "$ENVIRONMENT" == "dev" ]]; then
  SERVICES=("combined" "admin")
fi

# migrate is built + pushed alongside services so the standalone ECS task can pull it
BUILD_TARGETS=("${SERVICES[@]}" "migrate")

if [[ "$SERVICE" != "all" ]]; then
  SERVICES=("$SERVICE")
fi

echo "=== ShopCloud Deploy ==="
echo "Environment: ${ENVIRONMENT}"
echo "Services:    ${SERVICES[*]}"
echo "Region:      ${AWS_REGION}"
echo "========================"

# 1. Login to ECR
echo "[1/4] Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_BASE"

# 2. Build & push images (services + migrate)
echo "[2/4] Building and pushing images..."
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || date -u +%Y%m%d%H%M%S)
for svc in "${BUILD_TARGETS[@]}"; do
  IMAGE="${ECR_BASE}/shopcloud/${svc}:latest"
  TAG="${ECR_BASE}/shopcloud/${svc}:${GIT_SHA}"

  echo "  Building ${svc}..."
  docker build -t "$IMAGE" -t "$TAG" \
    --target "$svc" \
    -f app/Dockerfile app/

  echo "  Pushing ${svc}..."
  docker push "$IMAGE"
  docker push "$TAG"
done

# 3. Run migrations via ECS task; block until task exits; fail if exit code != 0
echo "[3/4] Running database migrations..."
TASK_DEF="shopcloud-${ENVIRONMENT}-migrate"
NETWORK_CONFIG=$(aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "${SERVICES[0]}" \
  --query 'services[0].networkConfiguration' \
  --output json)

TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --task-definition "$TASK_DEF" \
  --launch-type FARGATE \
  --network-configuration "$NETWORK_CONFIG" \
  --count 1 \
  --query 'tasks[0].taskArn' --output text --no-cli-pager)
echo "  Migration task: $TASK_ARN"

aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$TASK_ARN"
EXIT_CODE=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].exitCode' --output text)
if [[ "$EXIT_CODE" != "0" ]]; then
  echo "  Migration failed (exit ${EXIT_CODE})"
  exit 1
fi
echo "  Migration OK"

# 4. Update ECS services
echo "[4/4] Updating ECS services..."
for svc in "${SERVICES[@]}"; do
  echo "  Updating ${svc}..."
  aws ecs update-service \
    --cluster "$CLUSTER" \
    --service "$svc" \
    --force-new-deployment \
    --no-cli-pager
done

echo ""
echo "=== Deployment initiated ==="
echo "Monitor with: aws ecs describe-services --cluster ${CLUSTER} --services ${SERVICES[*]} --query 'services[].deployments'"
