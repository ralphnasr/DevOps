# WAF logging — log every WAF decision (BLOCK / ALLOW / COUNT) to CloudWatch
# so we can analyze blocked requests, identify attack patterns, and tune
# rules. Only the env that owns the WAF (prod / edge) creates this.

resource "aws_cloudwatch_log_group" "waf" {
  count             = var.waf_acl_arn == "" ? 0 : 1
  name              = "aws-waf-logs-shopcloud-${var.environment}"
  retention_in_days = 30
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count                   = var.waf_acl_arn == "" ? 0 : 1
  log_destination_configs = [aws_cloudwatch_log_group.waf[0].arn]
  resource_arn            = var.waf_acl_arn
}

# ── ECR scan-on-push: alert on critical findings ──
# scan-on-push is already enabled on each repo (Phase 2). This rule turns
# scan completions with at least one CRITICAL finding into an SNS page.

resource "aws_cloudwatch_event_rule" "ecr_critical_findings" {
  count       = var.create_account_singletons ? 1 : 0
  name        = "shopcloud-ecr-critical-findings"
  description = "Page on ECR image scan results with CRITICAL severity findings"

  event_pattern = jsonencode({
    source      = ["aws.ecr"]
    detail-type = ["ECR Image Scan"]
    detail = {
      "scan-status" = ["COMPLETE"]
      "finding-severity-counts" = {
        "CRITICAL" = [{ "numeric" = [">", 0] }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "ecr_critical_to_sns" {
  count     = var.create_account_singletons ? 1 : 0
  rule      = aws_cloudwatch_event_rule.ecr_critical_findings[0].name
  target_id = "alarms-sns"
  arn       = var.alarms_sns_topic_arn
}

# Allow EventBridge AND CloudWatch Alarms to publish to the SNS topic.
# aws_sns_topic_policy REPLACES the default policy, so CloudWatch loses its
# implicit access unless we add it back here. Without this, alarm actions
# fail with "CloudWatch Alarms is not authorized to perform: SNS:Publish".
data "aws_iam_policy_document" "sns_eventbridge_publish" {
  count = var.create_account_singletons ? 1 : 0

  statement {
    sid     = "AllowEventBridgePublish"
    actions = ["sns:Publish"]
    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
    resources = [var.alarms_sns_topic_arn]
  }

  statement {
    sid     = "AllowCloudWatchAlarmsPublish"
    actions = ["sns:Publish"]
    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }
    resources = [var.alarms_sns_topic_arn]
  }
}

resource "aws_sns_topic_policy" "events_publish" {
  count  = var.create_account_singletons ? 1 : 0
  arn    = var.alarms_sns_topic_arn
  policy = data.aws_iam_policy_document.sns_eventbridge_publish[0].json
}
