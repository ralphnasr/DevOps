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

variable "type" {
  type        = string
  description = "public or internal"
  default     = "public"
}

variable "name_suffix" {
  type    = string
  default = ""
}

variable "services" {
  type = map(object({
    port              = number
    health_check_path = string
    priority          = number
    path_patterns     = list(string)
  }))
}

variable "certificate_arn" {
  type    = string
  default = ""
}
