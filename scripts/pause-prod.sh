#!/usr/bin/env bash
# Scale prod ECS services to 0 + stop prod RDS to cut compute spend between demos.
# Safe to run repeatedly — idempotent (skips if already paused).
# AWS auto-restarts a stopped RDS after 7 days, so resume within a week.
set -euo pipefail

CLUSTER="shopcloud-prod"
SERVICES=(catalog cart checkout admin)
RDS_ID="shopcloud-prod"

echo "== Pausing prod (ECS + RDS) =="

for svc in "${SERVICES[@]}"; do
  current=$(aws ecs describe-services --cluster "$CLUSTER" --services "$svc" \
    --query 'services[0].desiredCount' --output text)
  if [ "$current" = "0" ]; then
    echo "  $svc already at 0 ✓"
  else
    echo "  Scaling $svc: $current -> 0"
    aws ecs update-service --cluster "$CLUSTER" --service "$svc" \
      --desired-count 0 --no-cli-pager > /dev/null
  fi
done

rds_status=$(aws rds describe-db-instances --db-instance-identifier "$RDS_ID" \
  --query 'DBInstances[0].DBInstanceStatus' --output text)
case "$rds_status" in
  available)
    echo "  Stopping RDS $RDS_ID"
    aws rds stop-db-instance --db-instance-identifier "$RDS_ID" --no-cli-pager > /dev/null
    ;;
  stopped|stopping)
    echo "  RDS already $rds_status ✓"
    ;;
  *)
    echo "  RDS in transient state ($rds_status) — skipping; re-run pause-prod.sh in 1 min"
    ;;
esac

echo ""
echo "Paused. Approx savings while down: ~\$2.50/day (~\$75/mo if always off)."
echo "Note: ALB, CloudFront, WAF, Redis, NAT keep running (~\$5/day baseline)."
echo "Resume with: ./scripts/resume-prod.sh"
