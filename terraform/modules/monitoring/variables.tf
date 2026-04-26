variable "environment" {
  type        = string
  description = "prod or dev"
}

variable "alarm_email" {
  type        = string
  description = "Email subscribed to the SNS alarms topic. Empty string skips subscription (useful for dev)."
  default     = ""
}

# ── ECS ──

variable "ecs_cluster_name" {
  type = string
}

variable "ecs_services" {
  type        = map(string)
  description = "Map of logical name → ECS service name. Each gets CPU + memory + running-task alarms."
}

# ── ALB ──

variable "alb_arn_suffix" {
  type        = string
  description = "ALB CloudWatch dimension value, e.g. app/shopcloud-prod-public/abc123. Computed from arn in main.tf."
}

variable "alb_target_group_arn_suffixes" {
  type        = map(string)
  description = "Map of logical name → target group dimension suffix (targetgroup/name/id) for unhealthy-host alarms."
  default     = {}
}

# ── RDS ──

variable "rds_instance_id" {
  type = string
}

variable "rds_has_replica" {
  type        = bool
  description = "Whether to create the cross-region replica lag alarm. True for prod only."
  default     = false
}

# ── ElastiCache ──

variable "elasticache_cluster_id" {
  type = string
}

# ── Lambda + SQS (prod only) ──

variable "lambda_function_name" {
  type        = string
  description = "Invoice Lambda name. Empty string disables Lambda alarms (dev has no invoice pipeline)."
  default     = ""
}

variable "sqs_dlq_name" {
  type        = string
  description = "DLQ queue name. Empty string disables DLQ alarm."
  default     = ""
}

# ── NAT ──

variable "nat_gateway_id" {
  type        = string
  description = "NAT gateway ID for the PacketsDropCount alarm. Empty string skips."
  default     = ""
}
