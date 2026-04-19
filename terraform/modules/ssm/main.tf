resource "aws_ssm_parameter" "db_url" {
  name  = "/${var.environment}/db/url"
  type  = "String"
  value = "postgresql+asyncpg://${var.rds_username}:${var.rds_password}@${var.rds_endpoint}:${var.rds_port}/${var.rds_db_name}"

  tags = { Name = "shopcloud-${var.environment}-db-url" }
}

resource "aws_ssm_parameter" "db_host" {
  name  = "/${var.environment}/db/host"
  type  = "String"
  value = var.rds_endpoint

  tags = { Name = "shopcloud-${var.environment}-db-host" }
}

resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.environment}/db/password"
  type  = "SecureString"
  value = var.rds_password

  tags = { Name = "shopcloud-${var.environment}-db-password" }
}

resource "aws_ssm_parameter" "redis_url" {
  name  = "/${var.environment}/redis/url"
  type  = "String"
  value = "redis://${var.redis_endpoint}:${var.redis_port}"

  tags = { Name = "shopcloud-${var.environment}-redis-url" }
}

resource "aws_ssm_parameter" "sqs_queue_url" {
  name  = "/${var.environment}/sqs/queue_url"
  type  = "String"
  value = var.sqs_queue_url != "" ? var.sqs_queue_url : "unset"

  tags = { Name = "shopcloud-${var.environment}-sqs-url" }
}

resource "aws_ssm_parameter" "s3_invoice_bucket" {
  name  = "/${var.environment}/s3/invoice_bucket"
  type  = "String"
  value = var.s3_invoice_bucket != "" ? var.s3_invoice_bucket : "unset"

  tags = { Name = "shopcloud-${var.environment}-s3-bucket" }
}

resource "aws_ssm_parameter" "cognito_customer_pool_id" {
  name  = "/${var.environment}/cognito/customer_pool_id"
  type  = "String"
  value = var.cognito_customer_pool_id

  tags = { Name = "shopcloud-${var.environment}-cognito-cust-pool" }
}

resource "aws_ssm_parameter" "cognito_customer_client_id" {
  name  = "/${var.environment}/cognito/customer_client_id"
  type  = "String"
  value = var.cognito_customer_client_id

  tags = { Name = "shopcloud-${var.environment}-cognito-cust-client" }
}

resource "aws_ssm_parameter" "cognito_admin_pool_id" {
  name  = "/${var.environment}/cognito/admin_pool_id"
  type  = "String"
  value = var.cognito_admin_pool_id

  tags = { Name = "shopcloud-${var.environment}-cognito-admin-pool" }
}

resource "aws_ssm_parameter" "cognito_admin_client_id" {
  name  = "/${var.environment}/cognito/admin_client_id"
  type  = "String"
  value = var.cognito_admin_client_id

  tags = { Name = "shopcloud-${var.environment}-cognito-admin-client" }
}
