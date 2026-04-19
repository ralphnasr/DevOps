variable "domain_prefix_suffix" {
  type    = string
  default = ""
}

variable "customer_callback_urls" {
  description = "OAuth callback URLs for customer app client — must be set from root to include the real CloudFront domain"
  type        = list(string)
}

variable "customer_logout_urls" {
  description = "Logout URLs for customer app client"
  type        = list(string)
}

variable "admin_callback_urls" {
  description = "OAuth callback URLs for admin app client"
  type        = list(string)
}

variable "admin_logout_urls" {
  description = "Logout URLs for admin app client"
  type        = list(string)
}
