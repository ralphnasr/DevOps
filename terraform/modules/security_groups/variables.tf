variable "vpc_id" {
  type = string
}

variable "environment" {
  type = string
}

variable "admin_cidr_blocks" {
  type    = list(string)
  default = []
}
