resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

locals {
  domain_suffix = var.domain_prefix_suffix != "" ? var.domain_prefix_suffix : random_string.suffix.result
}

# ── Customer User Pool ──

resource "aws_cognito_user_pool" "customer" {
  name = "shopcloud-customer"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  tags = { Name = "shopcloud-customer-pool" }
}

resource "aws_cognito_user_pool_client" "customer" {
  name         = "shopcloud-customer-client"
  user_pool_id = aws_cognito_user_pool.customer.id

  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = var.customer_callback_urls
  logout_urls   = var.customer_logout_urls

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

resource "aws_cognito_user_pool_domain" "customer" {
  domain       = "shopcloud-customer-${local.domain_suffix}"
  user_pool_id = aws_cognito_user_pool.customer.id
}

# ── Admin User Pool ──

resource "aws_cognito_user_pool" "admin" {
  name = "shopcloud-admin"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = false
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  tags = { Name = "shopcloud-admin-pool" }
}

resource "aws_cognito_user_pool_client" "admin" {
  name         = "shopcloud-admin-client"
  user_pool_id = aws_cognito_user_pool.admin.id

  generate_secret                      = false
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = var.admin_callback_urls
  logout_urls   = var.admin_logout_urls

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

resource "aws_cognito_user_pool_domain" "admin" {
  domain       = "shopcloud-admin-${local.domain_suffix}"
  user_pool_id = aws_cognito_user_pool.admin.id
}
