variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "shopcloud"
}

# ── VPC ──

variable "prod_vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "dev_vpc_cidr" {
  type    = string
  default = "10.1.0.0/16"
}

variable "prod_azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "dev_azs" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

# ── ECR ──

variable "ecr_service_names" {
  type    = list(string)
  default = ["catalog", "cart", "checkout", "admin", "migrate"]
}

# ── Cognito callback URLs ──
# Two-phase apply: first pass uses localhost only (CloudFront domain not yet
# known). Second pass overrides via -var to include the real CloudFront URL.
variable "customer_callback_urls" {
  type        = list(string)
  description = "OAuth callback URLs for the customer Cognito app client"
  default     = ["http://localhost:3000/callback.html"]
}

variable "customer_logout_urls" {
  type        = list(string)
  description = "Logout URLs for the customer Cognito app client"
  default     = ["http://localhost:3000/index.html"]
}

variable "admin_callback_urls" {
  type        = list(string)
  description = "OAuth callback URLs for the admin Cognito app client"
  default     = ["http://localhost:8001/admin"]
}

variable "admin_logout_urls" {
  type        = list(string)
  description = "Logout URLs for the admin Cognito app client"
  default     = ["http://localhost:8001/admin"]
}

# ── Bastion ──

variable "admin_cidr_blocks" {
  type        = list(string)
  description = "Whitelisted IPs for bastion SSH access"
  default     = []
}

variable "bastion_key_name" {
  type        = string
  description = "Name of the SSH key pair for bastion"
  default     = "shopcloud-bastion"
}

variable "bastion_public_key" {
  type        = string
  description = "SSH public key for bastion"
  default     = ""
}

# ── Domain ──

variable "domain_name" {
  type        = string
  description = "Optional custom domain for Route 53"
  default     = ""
}

# ── SES ──

variable "ses_verified_email" {
  type        = string
  description = "Verified sender email for invoices"
  default     = "noreply@shopcloud.example.com"
}
