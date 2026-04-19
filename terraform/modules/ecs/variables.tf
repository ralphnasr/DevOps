variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "cluster_name" {
  type = string
}

variable "ecr_urls" {
  type = map(string)
}

variable "services" {
  type = map(object({
    cpu               = number
    memory            = number
    desired_count     = number
    container_port    = number
    security_group_id = string
    target_group_arn  = string
  }))
}

variable "standalone_tasks" {
  description = "Task definitions without a service/LB/autoscaling (e.g. one-off migration tasks run via aws ecs run-task)"
  type = map(object({
    cpu    = number
    memory = number
  }))
  default = {}
}

variable "ssm_parameter_arns" {
  type    = list(string)
  default = []
}

variable "ssm_secrets" {
  description = "Map of environment variable name to SSM parameter ARN for container secrets"
  type        = map(string)
  default     = {}
}

variable "sqs_queue_arn" {
  description = "SQS queue ARN for scoped IAM permissions"
  type        = string
  default     = ""
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for scoped IAM permissions"
  type        = string
  default     = ""
}
