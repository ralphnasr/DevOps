output "parameter_arns" {
  value = [
    aws_ssm_parameter.db_url.arn,
    aws_ssm_parameter.db_host.arn,
    aws_ssm_parameter.db_password.arn,
    aws_ssm_parameter.redis_url.arn,
    aws_ssm_parameter.sqs_queue_url.arn,
    aws_ssm_parameter.s3_invoice_bucket.arn,
    aws_ssm_parameter.cognito_customer_pool_id.arn,
    aws_ssm_parameter.cognito_customer_client_id.arn,
    aws_ssm_parameter.cognito_admin_pool_id.arn,
    aws_ssm_parameter.cognito_admin_client_id.arn,
  ]
}

output "database_url_arn" {
  value = aws_ssm_parameter.db_url.arn
}

output "redis_url_arn" {
  value = aws_ssm_parameter.redis_url.arn
}

output "sqs_queue_url_arn" {
  value = aws_ssm_parameter.sqs_queue_url.arn
}

output "s3_invoice_bucket_arn" {
  value = aws_ssm_parameter.s3_invoice_bucket.arn
}

output "cognito_customer_pool_id_arn" {
  value = aws_ssm_parameter.cognito_customer_pool_id.arn
}

output "cognito_customer_client_id_arn" {
  value = aws_ssm_parameter.cognito_customer_client_id.arn
}

output "cognito_admin_pool_id_arn" {
  value = aws_ssm_parameter.cognito_admin_pool_id.arn
}

output "cognito_admin_client_id_arn" {
  value = aws_ssm_parameter.cognito_admin_client_id.arn
}
