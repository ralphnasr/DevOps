output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  value = aws_subnet.private_app[*].id
}

output "private_data_subnet_ids" {
  value = aws_subnet.private_data[*].id
}

output "nat_gateway_ip" {
  value = var.enable_nat_gateway ? aws_eip.nat[0].public_ip : ""
}

output "nat_gateway_id" {
  value = var.enable_nat_gateway ? aws_nat_gateway.main[0].id : ""
}

output "public_subnet_cidrs" {
  value = aws_subnet.public[*].cidr_block
}

output "private_app_subnet_cidrs" {
  value = aws_subnet.private_app[*].cidr_block
}

output "private_data_subnet_cidrs" {
  value = aws_subnet.private_data[*].cidr_block
}
