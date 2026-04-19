output "customer_pool_id" {
  value = aws_cognito_user_pool.customer.id
}

output "customer_client_id" {
  value = aws_cognito_user_pool_client.customer.id
}

output "customer_domain" {
  value = "https://${aws_cognito_user_pool_domain.customer.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}

output "admin_pool_id" {
  value = aws_cognito_user_pool.admin.id
}

output "admin_client_id" {
  value = aws_cognito_user_pool_client.admin.id
}

output "admin_domain" {
  value = "https://${aws_cognito_user_pool_domain.admin.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}

data "aws_region" "current" {}
