output "alb_arn" {
  value = aws_lb.main.arn
}

output "alb_dns_name" {
  value = aws_lb.main.dns_name
}

output "alb_zone_id" {
  value = aws_lb.main.zone_id
}

output "target_group_arns" {
  value = { for k, v in aws_lb_target_group.services : k => v.arn }
}

# CloudWatch ApplicationELB dimension format is "app/<name>/<id>" — exposed
# as arn_suffix so monitoring can wire it directly.
output "alb_arn_suffix" {
  value = aws_lb.main.arn_suffix
}

output "target_group_arn_suffixes" {
  value = { for k, v in aws_lb_target_group.services : k => v.arn_suffix }
}
