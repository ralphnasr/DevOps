variable "source_db_arn" {
  description = "ARN of the primary (source) RDS instance in the origin region (cross-region replica requires the full ARN)."
  type        = string
}

variable "instance_class" {
  description = "DR replica instance class. Matches primary for seamless failover; db.t3.micro for cost in demo."
  type        = string
  default     = "db.t3.micro"
}

variable "vpc_cidr" {
  description = "CIDR block for the minimal DR-only VPC in eu-west-1."
  type        = string
  default     = "10.2.0.0/16"
}
