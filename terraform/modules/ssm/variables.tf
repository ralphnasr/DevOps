variable "environment" {
  type = string
}

variable "rds_endpoint" {
  type = string
}

variable "rds_port" {
  type = number
}

variable "rds_db_name" {
  type = string
}

variable "rds_username" {
  type = string
}

variable "rds_password" {
  type      = string
  sensitive = true
}

variable "redis_endpoint" {
  type = string
}

variable "redis_port" {
  type = number
}

variable "sqs_queue_url" {
  type    = string
  default = ""
}

variable "s3_invoice_bucket" {
  type    = string
  default = ""
}

variable "cognito_customer_pool_id" {
  type = string
}

variable "cognito_customer_client_id" {
  type = string
}

variable "cognito_admin_pool_id" {
  type = string
}

variable "cognito_admin_client_id" {
  type = string
}
