output "flow_log_group_name" {
  value = aws_cloudwatch_log_group.flow_logs.name
}

output "cloudtrail_bucket" {
  value = var.create_account_singletons ? aws_s3_bucket.cloudtrail[0].id : ""
}

output "config_recorder_id" {
  value = var.create_account_singletons ? aws_config_configuration_recorder.main[0].id : ""
}

output "guardduty_detector_id" {
  value = var.create_account_singletons && var.enable_guardduty ? aws_guardduty_detector.main[0].id : ""
}

output "access_analyzer_arn" {
  value = var.create_account_singletons ? aws_accessanalyzer_analyzer.main[0].arn : ""
}

output "waf_log_group_name" {
  value = var.waf_acl_arn == "" ? "" : aws_cloudwatch_log_group.waf[0].name
}
