variable "environment" {
  type = string
}

# ── VPC + subnets (NACLs need both IDs and CIDRs) ──

variable "vpc_id" {
  type = string
}

variable "public_subnet_ids" {
  type = list(string)
}

variable "private_app_subnet_ids" {
  type = list(string)
}

variable "private_data_subnet_ids" {
  type = list(string)
}

variable "public_subnet_cidrs" {
  type = list(string)
}

variable "private_app_subnet_cidrs" {
  type = list(string)
}

variable "private_data_subnet_cidrs" {
  type = list(string)
}

variable "admin_cidr_blocks" {
  type    = list(string)
  default = []
}

# ── WAF (logging) — only the prod env passes this; dev passes "" ──

variable "waf_acl_arn" {
  type    = string
  default = ""
}

# ── Account-wide singletons (CloudTrail, GuardDuty, Config, IAM Analyzer) ──
# Set to true on exactly one environment (prod). Dev imports nothing global.

variable "create_account_singletons" {
  type        = bool
  description = "Create CloudTrail, GuardDuty detector, IAM Access Analyzer, AWS Config recorder. Only one env should set this."
  default     = false
}

variable "alarms_sns_topic_arn" {
  type        = string
  description = "SNS topic from monitoring module — ECR scan EventBridge rule sends critical findings here."
  default     = ""
}

# Independent gate so we can disable GuardDuty when the AWS account/IAM
# identity isn't subscribed to the service (returns SubscriptionRequiredException).
# The other singletons (CloudTrail, Config, Access Analyzer) are unaffected.
variable "enable_guardduty" {
  type        = bool
  description = "Provision the GuardDuty detector. Set false if the account isn't subscribed."
  default     = true
}
