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

rds_info=$(aws rds describe-db-instances --db-instance-identifier "$RDS_ID" \
  --query 'DBInstances[0].[DBInstanceStatus,ReadReplicaDBInstanceIdentifiers[0]]' \
  --output text)
rds_status=$(echo "$rds_info" | awk '{print $1}')
rds_replica=$(echo "$rds_info" | awk '{print $2}')

if [ -n "$rds_replica" ] && [ "$rds_replica" != "None" ]; then
  echo "  RDS $RDS_ID has a read-replica ($rds_replica) — skipping stop"
  echo "    (AWS blocks stopping a replica source; keeping DR intact is worth ~\$15/mo)"
else
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
fi

echo ""
echo "Paused. ECS @ 0 saves ~\$2/day; RDS stays up if a DR replica exists."
echo "Note: ALB, CloudFront, WAF, Redis, NAT keep running (~\$5/day baseline)."
echo "Resume with: ./scripts/resume-prod.sh"
