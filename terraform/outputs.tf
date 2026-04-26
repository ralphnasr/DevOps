# ── ECR ──
output "ecr_repository_urls" {
  value = module.ecr.repository_urls
}

# ── Cognito ──
output "cognito_customer_pool_id" {
  value = module.cognito.customer_pool_id
}

output "cognito_customer_client_id" {
  value = module.cognito.customer_client_id
}

output "cognito_customer_domain" {
  value = module.cognito.customer_domain
}

output "cognito_admin_pool_id" {
  value = module.cognito.admin_pool_id
}

output "cognito_admin_client_id" {
  value = module.cognito.admin_client_id
}

output "cognito_admin_domain" {
  value = module.cognito.admin_domain
}

# ── Production ──
output "prod_alb_dns" {
  value = module.prod_public_alb.alb_dns_name
}

output "prod_internal_alb_dns" {
  value = module.prod_internal_alb.alb_dns_name
}

output "prod_rds_endpoint" {
  value = module.prod_rds.endpoint
}

output "prod_rds_dr_replica_endpoint" {
  description = "Cross-region read replica in eu-west-1 — DR target + low-latency EU reads (Phase 1 §2.3)"
  value       = module.prod_rds_dr_replica.replica_endpoint
}

output "prod_rds_dr_replica_region" {
  value = module.prod_rds_dr_replica.replica_region
}

output "prod_redis_endpoint" {
  value = module.prod_elasticache.endpoint
}

output "prod_bastion_ip" {
  value = module.prod_bastion.bastion_public_ip
}

output "prod_ecs_cluster" {
  value = module.prod_ecs.ecs_cluster_name
}

output "cloudfront_domain" {
  value = module.edge.cloudfront_domain
}

output "cloudfront_distribution_id" {
  value = module.edge.cloudfront_distribution_id
}

output "s3_static_bucket" {
  value = module.edge.s3_static_bucket
}

output "waf_acl_arn" {
  value = module.edge.waf_acl_arn
}

# ── Development ──
output "dev_alb_dns" {
  value = module.dev_alb.alb_dns_name
}

output "dev_rds_endpoint" {
  value = module.dev_rds.endpoint
}

output "dev_redis_endpoint" {
  value = module.dev_elasticache.endpoint
}

output "dev_bastion_ip" {
  value = module.dev_bastion.bastion_public_ip
}

output "dev_ecs_cluster" {
  value = module.dev_ecs.ecs_cluster_name
}

# ── Phase 3: Monitoring ──
output "prod_dashboard_url" {
  value = module.prod_monitoring.dashboard_url
}

output "dev_dashboard_url" {
  value = module.dev_monitoring.dashboard_url
}

output "prod_alarms_topic_arn" {
  description = "SNS topic that all prod CloudWatch alarms publish to"
  value       = module.prod_monitoring.sns_topic_arn
}

output "dev_alarms_topic_arn" {
  value = module.dev_monitoring.sns_topic_arn
}

# ── Phase 3: Security ──
output "prod_flow_log_group" {
  value = module.prod_security.flow_log_group_name
}

output "dev_flow_log_group" {
  value = module.dev_security.flow_log_group_name
}

output "cloudtrail_bucket" {
  value = module.prod_security.cloudtrail_bucket
}

output "guardduty_detector_id" {
  value = module.prod_security.guardduty_detector_id
}

output "access_analyzer_arn" {
  value = module.prod_security.access_analyzer_arn
}

output "waf_log_group" {
  value = module.prod_security.waf_log_group_name
}
