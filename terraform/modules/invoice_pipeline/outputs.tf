output "sqs_queue_url" {
  value = aws_sqs_queue.orders.url
}

output "sqs_dlq_url" {
  value = aws_sqs_queue.dlq.url
}

output "s3_bucket_name" {
  value = aws_s3_bucket.invoices.id
}

output "sqs_queue_arn" {
  value = aws_sqs_queue.orders.arn
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.invoices.arn
}

output "lambda_function_arn" {
  value = aws_lambda_function.invoice.arn
}

output "ses_configuration_set_name" {
  value = aws_ses_configuration_set.main.name
}

output "ses_events_topic_arn" {
  value = aws_sns_topic.ses_events.arn
}

output "bounce_handler_function_arn" {
  value = aws_lambda_function.bounce_handler.arn
}

output "dashboard_name" {
  value = aws_cloudwatch_dashboard.ses.dashboard_name
}
