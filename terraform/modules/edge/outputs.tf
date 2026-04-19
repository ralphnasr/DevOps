output "cloudfront_domain" {
  value = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.main.id
}

output "s3_static_bucket" {
  value = aws_s3_bucket.static.id
}

output "waf_acl_arn" {
  value = aws_wafv2_web_acl.main.arn
}
