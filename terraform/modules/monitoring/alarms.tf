# All CloudWatch alarms for the environment. Every alarm sends to the SNS
# topic in main.tf. Thresholds match Phase 3 plan §4.2 — picked so a healthy
# system stays in OK state and only real degradation pages.

locals {
  sns_actions = [aws_sns_topic.alarms.arn]
}

# ── ECS service alarms (CPU, memory, running tasks) ──

resource "aws_cloudwatch_metric_alarm" "ecs_cpu_high" {
  for_each = var.ecs_services

  alarm_name          = "shopcloud-${var.environment}-${each.key}-cpu-high"
  alarm_description   = "${each.key} ECS service CPU > 80% for 10 min"
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = {
    # ECS publishes ServiceName as the short name (e.g. "cart"), which is
    # each.key in our map. each.value is the full task-def name like
    # "shopcloud-prod-cart" — wrong here. Caused tasks-low to stay stuck
    # in ALARM forever because no datapoints matched and treat_missing_data
    # is "breaching" for the running-tasks alarm.
    ClusterName = var.ecs_cluster_name
    ServiceName = each.key
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_memory_high" {
  for_each = var.ecs_services

  alarm_name          = "shopcloud-${var.environment}-${each.key}-memory-high"
  alarm_description   = "${each.key} ECS service memory > 80% for 10 min"
  namespace           = "AWS/ECS"
  metric_name         = "MemoryUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = {
    # ECS publishes ServiceName as the short name (e.g. "cart"), which is
    # each.key in our map. each.value is the full task-def name like
    # "shopcloud-prod-cart" — wrong here. Caused tasks-low to stay stuck
    # in ALARM forever because no datapoints matched and treat_missing_data
    # is "breaching" for the running-tasks alarm.
    ClusterName = var.ecs_cluster_name
    ServiceName = each.key
  }
}

resource "aws_cloudwatch_metric_alarm" "ecs_running_tasks_low" {
  for_each = var.ecs_services

  alarm_name          = "shopcloud-${var.environment}-${each.key}-tasks-low"
  alarm_description   = "${each.key} has zero running tasks (Fargate killed/crashed)"
  namespace           = "ECS/ContainerInsights"
  metric_name         = "RunningTaskCount"
  statistic           = "Minimum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = {
    # ECS publishes ServiceName as the short name (e.g. "cart"), which is
    # each.key in our map. each.value is the full task-def name like
    # "shopcloud-prod-cart" — wrong here. Caused tasks-low to stay stuck
    # in ALARM forever because no datapoints matched and treat_missing_data
    # is "breaching" for the running-tasks alarm.
    ClusterName = var.ecs_cluster_name
    ServiceName = each.key
  }
}

# ── ALB alarms (5xx, latency, unhealthy hosts, 4xx) ──

resource "aws_cloudwatch_metric_alarm" "alb_5xx" {
  alarm_name          = "shopcloud-${var.environment}-alb-5xx-errors"
  alarm_description   = "ALB target 5xx > 10 in 5 min — backend errors"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 10
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = { LoadBalancer = var.alb_arn_suffix }
}

resource "aws_cloudwatch_metric_alarm" "alb_4xx" {
  alarm_name          = "shopcloud-${var.environment}-alb-4xx-errors"
  alarm_description   = "ALB target 4xx > 100 in 5 min — possible attack or client misuse"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_4XX_Count"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 100
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { LoadBalancer = var.alb_arn_suffix }
}

resource "aws_cloudwatch_metric_alarm" "alb_latency_high" {
  alarm_name          = "shopcloud-${var.environment}-alb-latency-high"
  alarm_description   = "ALB p99 target response time > 5s for 10 min"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "TargetResponseTime"
  extended_statistic  = "p99"
  period              = 300
  evaluation_periods  = 2
  threshold           = 5
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { LoadBalancer = var.alb_arn_suffix }
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  for_each = var.alb_target_group_arn_suffixes

  alarm_name          = "shopcloud-${var.environment}-${each.key}-unhealthy-hosts"
  alarm_description   = "${each.key} target group has unhealthy targets for 3 min"
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = {
    TargetGroup  = each.value
    LoadBalancer = var.alb_arn_suffix
  }
}

# ── RDS alarms (CPU, connections, storage, latencies, replica lag) ──

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "shopcloud-${var.environment}-rds-cpu-high"
  alarm_description   = "RDS CPU > 80% for 15 min"
  namespace           = "AWS/RDS"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = { DBInstanceIdentifier = var.rds_instance_id }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "shopcloud-${var.environment}-rds-connections-high"
  alarm_description   = "RDS connections > 50 (db.t3.micro hard cap ≈ 60)"
  namespace           = "AWS/RDS"
  metric_name         = "DatabaseConnections"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 50
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { DBInstanceIdentifier = var.rds_instance_id }
}

resource "aws_cloudwatch_metric_alarm" "rds_storage_low" {
  alarm_name          = "shopcloud-${var.environment}-rds-storage-low"
  alarm_description   = "RDS free storage < 2 GB — CRITICAL, expand or clean up"
  namespace           = "AWS/RDS"
  metric_name         = "FreeStorageSpace"
  statistic           = "Minimum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 2147483648 # 2 GiB
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = { DBInstanceIdentifier = var.rds_instance_id }
}

resource "aws_cloudwatch_metric_alarm" "rds_read_latency" {
  alarm_name          = "shopcloud-${var.environment}-rds-read-latency-high"
  alarm_description   = "RDS read latency > 20 ms for 15 min"
  namespace           = "AWS/RDS"
  metric_name         = "ReadLatency"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 0.02
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { DBInstanceIdentifier = var.rds_instance_id }
}

resource "aws_cloudwatch_metric_alarm" "rds_write_latency" {
  alarm_name          = "shopcloud-${var.environment}-rds-write-latency-high"
  alarm_description   = "RDS write latency > 50 ms for 15 min"
  namespace           = "AWS/RDS"
  metric_name         = "WriteLatency"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 0.05
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { DBInstanceIdentifier = var.rds_instance_id }
}

resource "aws_cloudwatch_metric_alarm" "rds_replica_lag" {
  count = var.rds_has_replica ? 1 : 0

  alarm_name          = "shopcloud-${var.environment}-rds-replica-lag-high"
  alarm_description   = "Cross-region read replica lag > 60 s — DR target falling behind"
  namespace           = "AWS/RDS"
  metric_name         = "ReplicaLag"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 60
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { DBInstanceIdentifier = var.rds_instance_id }
}

# ── ElastiCache alarms (CPU, memory, evictions, connections) ──

resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "shopcloud-${var.environment}-redis-cpu-high"
  alarm_description   = "Redis CPU > 80% for 10 min"
  namespace           = "AWS/ElastiCache"
  metric_name         = "CPUUtilization"
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { CacheClusterId = var.elasticache_cluster_id }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "shopcloud-${var.environment}-redis-memory-high"
  alarm_description   = "Redis memory > 80% for 10 min"
  namespace           = "AWS/ElastiCache"
  metric_name         = "DatabaseMemoryUsagePercentage"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { CacheClusterId = var.elasticache_cluster_id }
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "shopcloud-${var.environment}-redis-evictions"
  alarm_description   = "Redis evicting keys — memory pressure, scale up cache.t3.micro"
  namespace           = "AWS/ElastiCache"
  metric_name         = "Evictions"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { CacheClusterId = var.elasticache_cluster_id }
}

resource "aws_cloudwatch_metric_alarm" "redis_connections" {
  alarm_name          = "shopcloud-${var.environment}-redis-connections-high"
  alarm_description   = "Redis connections > 50 — possible pool leak"
  namespace           = "AWS/ElastiCache"
  metric_name         = "CurrConnections"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 50
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { CacheClusterId = var.elasticache_cluster_id }
}

# ── Lambda alarms (errors, duration, throttles) — prod only ──

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  count = var.lambda_function_name == "" ? 0 : 1

  alarm_name          = "shopcloud-${var.environment}-lambda-invoice-errors"
  alarm_description   = "Invoice Lambda errors > 3 in 5 min"
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 3
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = { FunctionName = var.lambda_function_name }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  count = var.lambda_function_name == "" ? 0 : 1

  alarm_name          = "shopcloud-${var.environment}-lambda-invoice-duration-high"
  alarm_description   = "Invoice Lambda duration > 25 s — approaching 30 s timeout"
  namespace           = "AWS/Lambda"
  metric_name         = "Duration"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 25000
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { FunctionName = var.lambda_function_name }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  count = var.lambda_function_name == "" ? 0 : 1

  alarm_name          = "shopcloud-${var.environment}-lambda-invoice-throttles"
  alarm_description   = "Invoice Lambda throttled — concurrency limit hit"
  namespace           = "AWS/Lambda"
  metric_name         = "Throttles"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { FunctionName = var.lambda_function_name }
}

# ── SQS DLQ depth — prod only ──
# Note: invoice_pipeline already defines its own DLQ alarm wired to the SES SNS
# topic. This duplicate routes to the central alarms topic so on-call gets
# paged through the same channel as everything else.

resource "aws_cloudwatch_metric_alarm" "sqs_dlq" {
  count = var.sqs_dlq_name == "" ? 0 : 1

  alarm_name          = "shopcloud-${var.environment}-dlq-not-empty-central"
  alarm_description   = "Invoice DLQ has messages — failed PDF generation or SES reject"
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions
  ok_actions          = local.sns_actions

  dimensions = { QueueName = var.sqs_dlq_name }
}

# ── NAT Gateway — packet drops indicate NAT congestion ──

resource "aws_cloudwatch_metric_alarm" "nat_packet_drops" {
  count = var.nat_gateway_id == "" ? 0 : 1

  alarm_name          = "shopcloud-${var.environment}-nat-packet-drops"
  alarm_description   = "NAT gateway dropping packets — congestion or port exhaustion"
  namespace           = "AWS/NATGateway"
  metric_name         = "PacketsDropCount"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = local.sns_actions

  dimensions = { NatGatewayId = var.nat_gateway_id }
}
