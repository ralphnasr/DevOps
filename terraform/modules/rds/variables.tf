variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "security_group_id" {
  type = string
}

variable "instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "allocated_storage" {
  type    = number
  default = 20
}

variable "multi_az" {
  type    = bool
  default = false
}

variable "backup_retention_period" {
  type    = number
  default = 7
}

variable "db_name" {
  type    = string
  default = "shopcloud"
}

variable "master_username" {
  type    = string
  default = "shopcloud_admin"
}

variable "deletion_protection" {
  type    = bool
  default = false
}
