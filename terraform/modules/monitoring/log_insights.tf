# 8 saved CloudWatch Logs Insights queries — one per common ops question.
# Names follow the README so docs and console agree. Queries scan the JSON
# log fields the FastAPI services and Lambdas emit (level, msg, request_id,
# path, status_code, duration_ms, etc.).

locals {
  # ECS log groups follow the convention /ecs/shopcloud-<env>/<service>.
  ecs_log_groups = [
    for k, v in var.ecs_services :
    "/ecs/shopcloud-${var.environment}/${k}"
  ]

  # Lambda log groups — only when prod has the invoice pipeline wired.
  lambda_log_groups = var.lambda_function_name == "" ? [] : [
    "/aws/lambda/${var.lambda_function_name}",
    "/aws/lambda/shopcloud-${var.environment}-bounce-handler",
  ]

  all_app_log_groups = concat(local.ecs_log_groups, local.lambda_log_groups)
}

resource "aws_cloudwatch_query_definition" "errors_last_hour" {
  name            = "shopcloud-${var.environment}/errors-last-hour"
  log_group_names = local.all_app_log_groups
  query_string    = <<-EOQ
    fields @timestamp, @log, level, msg, request_id, path, status_code
    | filter level = "ERROR" or status_code >= 500
    | sort @timestamp desc
    | limit 200
  EOQ
}

resource "aws_cloudwatch_query_definition" "slow_requests_p95" {
  name            = "shopcloud-${var.environment}/slow-requests-p95"
  log_group_names = local.ecs_log_groups
  query_string    = <<-EOQ
    fields @timestamp, path, duration_ms
    | filter ispresent(duration_ms)
    | stats count() as requests, avg(duration_ms) as avg_ms, pct(duration_ms, 95) as p95_ms, max(duration_ms) as max_ms by path
    | sort p95_ms desc
    | limit 50
  EOQ
}

resource "aws_cloudwatch_query_definition" "auth_failures" {
  name            = "shopcloud-${var.environment}/auth-failures"
  log_group_names = local.ecs_log_groups
  query_string    = <<-EOQ
    fields @timestamp, msg, path, status_code, error
    | filter status_code = 401 or status_code = 403 or msg like /JWT/ or msg like /Cognito/ or msg like /unauthorized/
    | sort @timestamp desc
    | limit 200
  EOQ
}

resource "aws_cloudwatch_query_definition" "cart_redis_errors" {
  name            = "shopcloud-${var.environment}/cart-redis-errors"
  log_group_names = ["/ecs/shopcloud-${var.environment}/cart"]
  query_string    = <<-EOQ
    fields @timestamp, level, msg, error
    | filter level = "ERROR" or msg like /redis/ or msg like /Redis/ or msg like /connection/
    | sort @timestamp desc
    | limit 200
  EOQ
}

resource "aws_cloudwatch_query_definition" "checkout_failures" {
  name            = "shopcloud-${var.environment}/checkout-failures"
  log_group_names = ["/ecs/shopcloud-${var.environment}/checkout"]
  query_string    = <<-EOQ
    fields @timestamp, level, msg, order_id, customer_id, error
    | filter level = "ERROR" or msg like /checkout/ or msg like /oversell/ or msg like /coupon/
    | sort @timestamp desc
    | limit 200
  EOQ
}

resource "aws_cloudwatch_query_definition" "lambda_invoice_errors" {
  count           = var.lambda_function_name == "" ? 0 : 1
  name            = "shopcloud-${var.environment}/lambda-invoice-errors"
  log_group_names = ["/aws/lambda/${var.lambda_function_name}"]
  query_string    = <<-EOQ
    fields @timestamp, @message, @requestId
    | filter @message like /ERROR/ or @message like /Exception/ or @message like /Traceback/ or @message like /SES/
    | sort @timestamp desc
    | limit 200
  EOQ
}

resource "aws_cloudwatch_query_definition" "dlq_replay_trace" {
  count           = var.lambda_function_name == "" ? 0 : 1
  name            = "shopcloud-${var.environment}/dlq-replay-trace"
  log_group_names = ["/aws/lambda/${var.lambda_function_name}"]
  query_string    = <<-EOQ
    fields @timestamp, @requestId, @message
    | filter @message like /order_id/
    | parse @message /order_id[=:]\s*"?(?<order_id>[\w-]+)"?/
    | sort @timestamp desc
    | limit 200
  EOQ
}

resource "aws_cloudwatch_query_definition" "admin_access_audit" {
  name            = "shopcloud-${var.environment}/admin-access-audit"
  log_group_names = ["/ecs/shopcloud-${var.environment}/admin"]
  query_string    = <<-EOQ
    fields @timestamp, actor, action, entity_type, entity_id, path, status_code
    | filter ispresent(actor) or path like /admin/
    | sort @timestamp desc
    | limit 200
  EOQ
}
