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
