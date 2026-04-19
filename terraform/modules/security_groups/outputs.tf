output "public_alb_sg_id" {
  value = aws_security_group.public_alb.id
}

output "customer_fargate_sg_id" {
  value = aws_security_group.customer_fargate.id
}

output "internal_alb_sg_id" {
  value = aws_security_group.internal_alb.id
}

output "admin_fargate_sg_id" {
  value = aws_security_group.admin_fargate.id
}

output "rds_sg_id" {
  value = aws_security_group.rds.id
}

output "elasticache_sg_id" {
  value = aws_security_group.elasticache.id
}

output "bastion_sg_id" {
  value = aws_security_group.bastion.id
}

output "lambda_sg_id" {
  value = aws_security_group.lambda.id
}
