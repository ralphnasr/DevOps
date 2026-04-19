#!/usr/bin/env bash
# Bring prod back up after pause-prod.sh.
# Order matters: RDS must be available before ECS tasks can pass health checks.
# Wall time: ~7-10 min (RDS ~5-7m + ECS rollout ~2m + health-check warmup).
set -euo pipefail

CLUSTER="shopcloud-prod"
SERVICES=(catalog cart checkout admin)
RDS_ID="shopcloud-prod"
CF_URL="https://d3w3kfhcnfq6gy.cloudfront.net"

echo "== Resuming prod =="

rds_status=$(aws rds describe-db-instances --db-instance-identifier "$RDS_ID" \
  --query 'DBInstances[0].DBInstanceStatus' --output text)
case "$rds_status" in
  stopped)
    echo "  Starting RDS $RDS_ID"
    aws rds start-db-instance --db-instance-identifier "$RDS_ID" --no-cli-pager > /dev/null
    ;;
  available)
    echo "  RDS already available ✓"
    ;;
  starting|configuring*|backing-up|modifying)
    echo "  RDS already $rds_status — will wait"
    ;;
  *)
    echo "  ERROR: RDS in unexpected state: $rds_status"
    exit 1
    ;;
esac

echo "  Waiting for RDS available (5-7 min)..."
aws rds wait db-instance-available --db-instance-identifier "$RDS_ID"
echo "  RDS available ✓"

for svc in "${SERVICES[@]}"; do
  current=$(aws ecs describe-services --cluster "$CLUSTER" --services "$svc" \
    --query 'services[0].desiredCount' --output text)
  if [ "$current" = "1" ]; then
    echo "  $svc already at 1 ✓"
  else
    echo "  Scaling $svc: $current -> 1"
    aws ecs update-service --cluster "$CLUSTER" --service "$svc" \
      --desired-count 1 --no-cli-pager > /dev/null
  fi
done

echo "  Waiting for ECS services stable (2-3 min)..."
aws ecs wait services-stable --cluster "$CLUSTER" --services "${SERVICES[@]}"
echo "  ECS stable ✓"

echo "  Smoke-testing API..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" "$CF_URL/api/products?limit=1")
if [ "$http_code" = "200" ]; then
  echo "  API responding 200 ✓"
else
  echo "  WARNING: API returned $http_code — check CloudWatch logs"
fi

echo ""
echo "Resumed. Storefront: $CF_URL"
