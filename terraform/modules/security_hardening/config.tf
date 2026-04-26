# AWS Config — account-wide singleton (lives only in the env that owns
# create_account_singletons). Continuously evaluates resource configurations
# against AWS-managed compliance rules and flags drift.

# ── S3 bucket for Config snapshots ──

resource "aws_s3_bucket" "config" {
  count         = var.create_account_singletons ? 1 : 0
  bucket        = "shopcloud-config-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = { Name = "shopcloud-config" }
}

resource "aws_s3_bucket_public_access_block" "config" {
  count                   = var.create_account_singletons ? 1 : 0
  bucket                  = aws_s3_bucket.config[0].id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "config" {
  count  = var.create_account_singletons ? 1 : 0
  bucket = aws_s3_bucket.config[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AWSConfigBucketPermissionsCheck"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:GetBucketAcl"
        Resource  = aws_s3_bucket.config[0].arn
      },
      {
        Sid       = "AWSConfigBucketExistenceCheck"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:ListBucket"
        Resource  = aws_s3_bucket.config[0].arn
      },
      {
        Sid       = "AWSConfigBucketDelivery"
        Effect    = "Allow"
        Principal = { Service = "config.amazonaws.com" }
        Action    = "s3:PutObject"
        Resource  = "${aws_s3_bucket.config[0].arn}/AWSLogs/${data.aws_caller_identity.current.account_id}/Config/*"
        Condition = {
          StringEquals = { "s3:x-amz-acl" = "bucket-owner-full-control" }
        }
      }
    ]
  })
}

# ── IAM role Config assumes ──

resource "aws_iam_role" "config" {
  count = var.create_account_singletons ? 1 : 0
  name  = "shopcloud-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "config.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "config_managed" {
  count      = var.create_account_singletons ? 1 : 0
  role       = aws_iam_role.config[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

# ── Recorder, delivery channel, status ──

resource "aws_config_configuration_recorder" "main" {
  count    = var.create_account_singletons ? 1 : 0
  name     = "shopcloud-recorder"
  role_arn = aws_iam_role.config[0].arn

  recording_group {
    all_supported                 = true
    include_global_resource_types = true
  }
}

resource "aws_config_delivery_channel" "main" {
  count          = var.create_account_singletons ? 1 : 0
  name           = "shopcloud-delivery"
  s3_bucket_name = aws_s3_bucket.config[0].id

  depends_on = [
    aws_config_configuration_recorder.main,
    aws_s3_bucket_policy.config,
  ]
}

resource "aws_config_configuration_recorder_status" "main" {
  count      = var.create_account_singletons ? 1 : 0
  name       = aws_config_configuration_recorder.main[0].name
  is_enabled = true
  depends_on = [aws_config_delivery_channel.main]
}

# ── 9 managed rules ──

locals {
  config_managed_rules = var.create_account_singletons ? {
    s3_public_read     = "S3_BUCKET_PUBLIC_READ_PROHIBITED"
    s3_public_write    = "S3_BUCKET_PUBLIC_WRITE_PROHIBITED"
    rds_encrypted      = "RDS_STORAGE_ENCRYPTED"
    rds_public_access  = "RDS_INSTANCE_PUBLIC_ACCESS_CHECK"
    vpc_default_sg     = "VPC_DEFAULT_SECURITY_GROUP_CLOSED"
    restricted_ssh     = "INCOMING_SSH_DISABLED"
    ecs_nonroot        = "ECS_TASK_DEFINITION_NONROOT_USER"
    cloudtrail_cw_logs = "CLOUD_TRAIL_CLOUD_WATCH_LOGS_ENABLED"
    root_mfa           = "ROOT_ACCOUNT_MFA_ENABLED"
  } : {}
}

resource "aws_config_config_rule" "managed" {
  for_each = local.config_managed_rules

  name = replace(each.key, "_", "-")

  source {
    owner             = "AWS"
    source_identifier = each.value
  }

  depends_on = [aws_config_configuration_recorder_status.main]
}
