# shopcloud-{env}-overview dashboard. 5 rows × 3 widgets = 15 widgets, one per
# critical signal (service health, errors/latency, compute, data layer, async).
# Lambda + SQS widgets are blank when not provisioned (dev) but the row stays
# so the layout is consistent across environments.

locals {
  region = data.aws_region.current.name

  # ECS metrics — one line per service. Built dynamically from the service map
  # so adding a service automatically adds a line.
  ecs_running_metrics = [
    for k, v in var.ecs_services :
    ["ECS/ContainerInsights", "RunningTaskCount", "ClusterName", var.ecs_cluster_name, "ServiceName", v]
  ]
  ecs_cpu_metrics = [
    for k, v in var.ecs_services :
    ["AWS/ECS", "CPUUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", v]
  ]
  ecs_mem_metrics = [
    for k, v in var.ecs_services :
    ["AWS/ECS", "MemoryUtilization", "ClusterName", var.ecs_cluster_name, "ServiceName", v]
  ]

  tg_healthy_metrics = [
    for k, v in var.alb_target_group_arn_suffixes :
    ["AWS/ApplicationELB", "HealthyHostCount", "TargetGroup", v, "LoadBalancer", var.alb_arn_suffix]
  ]
}

data "aws_region" "current" {}

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "shopcloud-${var.environment}-overview"

  dashboard_body = jsonencode({
    widgets = [
      # ── Row 1: Service health ──
      {
        type = "metric"
        x    = 0, y = 0, width = 8, height = 6
        properties = {
          title   = "ECS Running Tasks"
          metrics = local.ecs_running_metrics
          region  = local.region
          period  = 60
          stat    = "Average"
          view    = "timeSeries"
          stacked = false
        }
      },
      {
        type = "metric"
        x    = 8, y = 0, width = 8, height = 6
        properties = {
          title   = "ALB Healthy Hosts (per target group)"
          metrics = local.tg_healthy_metrics
          region  = local.region
          period  = 60
          stat    = "Minimum"
          view    = "timeSeries"
        }
      },
      {
        type = "metric"
        x    = 16, y = 0, width = 8, height = 6
        properties = {
          title = "ALB Request Count"
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.alb_arn_suffix]
          ]
          region = local.region
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },

      # ── Row 2: Latency & errors ──
      {
        type = "metric"
        x    = 0, y = 6, width = 8, height = 6
        properties = {
          title = "ALB Target Response Time (p50/p90/p99)"
          metrics = [
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", var.alb_arn_suffix, { stat = "p50", label = "p50" }],
            ["...", { stat = "p90", label = "p90" }],
            ["...", { stat = "p99", label = "p99" }]
          ]
          region = local.region
          period = 60
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        x    = 8, y = 6, width = 8, height = 6
        properties = {
          title = "ALB 5xx Errors"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", var.alb_arn_suffix],
            [".", "HTTPCode_ELB_5XX_Count", ".", "."]
          ]
          region = local.region
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        x    = 16, y = 6, width = 8, height = 6
        properties = {
          title = "ALB 4xx Errors"
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_Target_4XX_Count", "LoadBalancer", var.alb_arn_suffix],
            [".", "HTTPCode_ELB_4XX_Count", ".", "."]
          ]
          region = local.region
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },

      # ── Row 3: Compute resources ──
      {
        type = "metric"
        x    = 0, y = 12, width = 8, height = 6
        properties = {
          title   = "ECS CPU Utilization"
          metrics = local.ecs_cpu_metrics
          region  = local.region
          period  = 300
          stat    = "Average"
          view    = "timeSeries"
          yAxis   = { left = { min = 0, max = 100 } }
        }
      },
      {
        type = "metric"
        x    = 8, y = 12, width = 8, height = 6
        properties = {
          title   = "ECS Memory Utilization"
          metrics = local.ecs_mem_metrics
          region  = local.region
          period  = 300
          stat    = "Average"
          view    = "timeSeries"
          yAxis   = { left = { min = 0, max = 100 } }
        }
      },
      {
        type = "metric"
        x    = 16, y = 12, width = 8, height = 6
        properties = {
          title = "Lambda Duration + Errors"
          metrics = var.lambda_function_name == "" ? [] : [
            ["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_name, { stat = "Average", label = "avg duration ms" }],
            [".", "Errors", ".", ".", { stat = "Sum", label = "errors", yAxis = "right" }]
          ]
          region = local.region
          period = 300
          view   = "timeSeries"
        }
      },

      # ── Row 4: Data layer ──
      {
        type = "metric"
        x    = 0, y = 18, width = 8, height = 6
        properties = {
          title = "RDS CPU + Connections"
          metrics = [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.rds_instance_id, { stat = "Average", label = "CPU %" }],
            [".", "DatabaseConnections", ".", ".", { stat = "Maximum", label = "connections", yAxis = "right" }]
          ]
          region = local.region
          period = 300
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        x    = 8, y = 18, width = 8, height = 6
        properties = {
          title = "RDS Free Storage (GB)"
          metrics = [
            ["AWS/RDS", "FreeStorageSpace", "DBInstanceIdentifier", var.rds_instance_id]
          ]
          region = local.region
          period = 300
          stat   = "Minimum"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        x    = 16, y = 18, width = 8, height = 6
        properties = {
          title = "Redis Memory % + Evictions"
          metrics = [
            ["AWS/ElastiCache", "DatabaseMemoryUsagePercentage", "CacheClusterId", var.elasticache_cluster_id, { stat = "Maximum", label = "memory %" }],
            [".", "Evictions", ".", ".", { stat = "Sum", label = "evictions", yAxis = "right" }]
          ]
          region = local.region
          period = 300
          view   = "timeSeries"
        }
      },

      # ── Row 5: Async pipeline ──
      {
        type = "metric"
        x    = 0, y = 24, width = 8, height = 6
        properties = {
          title = "SQS Messages (sent / received)"
          metrics = var.sqs_dlq_name == "" ? [] : [
            ["AWS/SQS", "NumberOfMessagesSent", "QueueName", replace(var.sqs_dlq_name, "-dlq", "")],
            [".", "NumberOfMessagesReceived", ".", "."]
          ]
          region = local.region
          period = 300
          stat   = "Sum"
          view   = "timeSeries"
        }
      },
      {
        type = "metric"
        x    = 8, y = 24, width = 8, height = 6
        properties = {
          title = "DLQ Depth"
          metrics = var.sqs_dlq_name == "" ? [] : [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.sqs_dlq_name]
          ]
          region = local.region
          period = 60
          stat   = "Maximum"
          view   = "singleValue"
        }
      },
      {
        type = "metric"
        x    = 16, y = 24, width = 8, height = 6
        properties = {
          title = "Lambda Invocations + Errors"
          metrics = var.lambda_function_name == "" ? [] : [
            ["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_name],
            [".", "Errors", ".", "."],
            [".", "Throttles", ".", "."]
          ]
          region  = local.region
          period  = 300
          stat    = "Sum"
          view    = "timeSeries"
          stacked = true
        }
      }
    ]
  })
}
