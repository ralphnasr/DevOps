# ══════════════════════════════════════════════════════════════
# ShopCloud Infrastructure — Root Module
# ══════════════════════════════════════════════════════════════

# ── Shared (account-level) ──

module "ecr" {
  source        = "./modules/ecr"
  service_names = var.ecr_service_names
}

module "cognito" {
  source = "./modules/cognito"

  customer_callback_urls = var.customer_callback_urls
  customer_logout_urls   = var.customer_logout_urls
  admin_callback_urls    = var.admin_callback_urls
  admin_logout_urls      = var.admin_logout_urls
}

# ══════════════════════════════════════════════════════════════
# PRODUCTION ENVIRONMENT
# ══════════════════════════════════════════════════════════════

module "prod_vpc" {
  source                    = "./modules/vpc"
  environment               = "prod"
  vpc_cidr                  = var.prod_vpc_cidr
  azs                       = var.prod_azs
  public_subnet_cidrs       = ["10.0.1.0/24", "10.0.2.0/24"]
  private_app_subnet_cidrs  = ["10.0.10.0/24", "10.0.20.0/24"]
  private_data_subnet_cidrs = ["10.0.30.0/24", "10.0.40.0/24"]
  enable_nat_gateway        = true
}

module "prod_sg" {
  source            = "./modules/security_groups"
  environment       = "prod"
  vpc_id            = module.prod_vpc.vpc_id
  admin_cidr_blocks = var.admin_cidr_blocks
}

module "prod_public_alb" {
  source            = "./modules/alb"
  environment       = "prod"
  vpc_id            = module.prod_vpc.vpc_id
  subnet_ids        = module.prod_vpc.public_subnet_ids
  security_group_id = module.prod_sg.public_alb_sg_id
  type              = "public"
  services = {
    catalog = {
      port              = 8000
      health_check_path = "/health"
      priority          = 100
      path_patterns     = ["/api/products", "/api/products/*"]
    }
    cart = {
      port              = 8000
      health_check_path = "/health"
      priority          = 200
      path_patterns     = ["/api/cart", "/api/cart/*"]
    }
    checkout = {
      port              = 8000
      health_check_path = "/health"
      priority          = 300
      path_patterns     = ["/api/checkout", "/api/orders", "/api/orders/*"]
    }
  }
}

module "prod_internal_alb" {
  source            = "./modules/alb"
  environment       = "prod"
  vpc_id            = module.prod_vpc.vpc_id
  subnet_ids        = module.prod_vpc.private_app_subnet_ids
  security_group_id = module.prod_sg.internal_alb_sg_id
  type              = "internal"
  name_suffix       = "internal"
  services = {
    admin = {
      port              = 8000
      health_check_path = "/health"
      priority          = 100
      path_patterns     = ["/admin", "/admin/*"]
    }
  }
}

module "prod_rds" {
  source                  = "./modules/rds"
  environment             = "prod"
  vpc_id                  = module.prod_vpc.vpc_id
  subnet_ids              = module.prod_vpc.private_data_subnet_ids
  security_group_id       = module.prod_sg.rds_sg_id
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  multi_az                = true # synchronous standby in second AZ for auto-failover (project HA requirement)
  backup_retention_period = 1    # minimum non-zero retention (this AWS Free Tier account rejects 7+); raise to 35 once off Free Tier
  deletion_protection     = true # block accidental drop of prod data
}

module "prod_rds_dr_replica" {
  source = "./modules/rds_dr_replica"

  providers = {
    aws = aws.eu_west_1
  }

  source_db_arn  = module.prod_rds.db_instance_arn
  instance_class = "db.t3.micro"
}

module "prod_elasticache" {
  source            = "./modules/elasticache"
  environment       = "prod"
  subnet_ids        = module.prod_vpc.private_data_subnet_ids
  security_group_id = module.prod_sg.elasticache_sg_id
  node_type         = "cache.t3.micro"
}

module "prod_bastion" {
  source            = "./modules/bastion"
  environment       = "prod"
  vpc_id            = module.prod_vpc.vpc_id
  subnet_id         = module.prod_vpc.public_subnet_ids[0]
  security_group_id = module.prod_sg.bastion_sg_id
  key_pair_name     = var.bastion_key_name
  public_key        = var.bastion_public_key
}

module "prod_ssm" {
  source                     = "./modules/ssm"
  environment                = "prod"
  rds_endpoint               = module.prod_rds.endpoint
  rds_port                   = module.prod_rds.port
  rds_db_name                = module.prod_rds.db_name
  rds_username               = module.prod_rds.master_username
  rds_password               = module.prod_rds.master_password
  redis_endpoint             = module.prod_elasticache.endpoint
  redis_port                 = module.prod_elasticache.port
  sqs_queue_url              = module.prod_invoice.sqs_queue_url
  s3_invoice_bucket          = module.prod_invoice.s3_bucket_name
  cognito_customer_pool_id   = module.cognito.customer_pool_id
  cognito_customer_client_id = module.cognito.customer_client_id
  cognito_admin_pool_id      = module.cognito.admin_pool_id
  cognito_admin_client_id    = module.cognito.admin_client_id
}

module "prod_ecs" {
  source       = "./modules/ecs"
  environment  = "prod"
  vpc_id       = module.prod_vpc.vpc_id
  subnet_ids   = module.prod_vpc.private_app_subnet_ids
  cluster_name = "shopcloud-prod"
  ecr_urls     = module.ecr.repository_urls

  services = {
    catalog = {
      cpu               = 512
      memory            = 1024
      desired_count     = 1
      container_port    = 8000
      security_group_id = module.prod_sg.customer_fargate_sg_id
      target_group_arn  = module.prod_public_alb.target_group_arns["catalog"]
    }
    cart = {
      cpu               = 512
      memory            = 1024
      desired_count     = 1
      container_port    = 8000
      security_group_id = module.prod_sg.customer_fargate_sg_id
      target_group_arn  = module.prod_public_alb.target_group_arns["cart"]
    }
    checkout = {
      cpu               = 512
      memory            = 1024
      desired_count     = 1
      container_port    = 8000
      security_group_id = module.prod_sg.customer_fargate_sg_id
      target_group_arn  = module.prod_public_alb.target_group_arns["checkout"]
    }
    admin = {
      cpu               = 256
      memory            = 512
      desired_count     = 1
      container_port    = 8000
      security_group_id = module.prod_sg.admin_fargate_sg_id
      target_group_arn  = module.prod_internal_alb.target_group_arns["admin"]
    }
  }

  standalone_tasks = {
    migrate = {
      cpu    = 256
      memory = 512
    }
  }

  ssm_parameter_arns = module.prod_ssm.parameter_arns

  ssm_secrets = {
    DATABASE_URL            = module.prod_ssm.database_url_arn
    REDIS_URL               = module.prod_ssm.redis_url_arn
    SQS_QUEUE_URL           = module.prod_ssm.sqs_queue_url_arn
    S3_INVOICE_BUCKET       = module.prod_ssm.s3_invoice_bucket_arn
    COGNITO_USER_POOL_ID    = module.prod_ssm.cognito_customer_pool_id_arn
    COGNITO_APP_CLIENT_ID   = module.prod_ssm.cognito_customer_client_id_arn
    COGNITO_ADMIN_POOL_ID   = module.prod_ssm.cognito_admin_pool_id_arn
    COGNITO_ADMIN_CLIENT_ID = module.prod_ssm.cognito_admin_client_id_arn
  }

  sqs_queue_arn = module.prod_invoice.sqs_queue_arn
  s3_bucket_arn = module.prod_invoice.s3_bucket_arn
}

module "prod_invoice" {
  source             = "./modules/invoice_pipeline"
  environment        = "prod"
  vpc_id             = module.prod_vpc.vpc_id
  subnet_ids         = module.prod_vpc.private_app_subnet_ids
  security_group_id  = module.prod_sg.lambda_sg_id
  rds_endpoint       = module.prod_rds.endpoint
  rds_db_name        = module.prod_rds.db_name
  rds_username       = module.prod_rds.master_username
  rds_password       = module.prod_rds.master_password
  ses_verified_email = var.ses_verified_email
}

module "edge" {
  source       = "./modules/edge"
  domain_name  = var.domain_name
  alb_dns_name = module.prod_public_alb.alb_dns_name
}

# ══════════════════════════════════════════════════════════════
# DEVELOPMENT ENVIRONMENT
# ══════════════════════════════════════════════════════════════

module "dev_vpc" {
  source                    = "./modules/vpc"
  environment               = "dev"
  vpc_cidr                  = var.dev_vpc_cidr
  azs                       = var.dev_azs
  public_subnet_cidrs       = ["10.1.1.0/24", "10.1.2.0/24"]
  private_app_subnet_cidrs  = ["10.1.10.0/24", "10.1.20.0/24"]
  private_data_subnet_cidrs = ["10.1.30.0/24", "10.1.40.0/24"]
  enable_nat_gateway        = true
}

module "dev_sg" {
  source            = "./modules/security_groups"
  environment       = "dev"
  vpc_id            = module.dev_vpc.vpc_id
  admin_cidr_blocks = var.admin_cidr_blocks
}

module "dev_alb" {
  source            = "./modules/alb"
  environment       = "dev"
  vpc_id            = module.dev_vpc.vpc_id
  subnet_ids        = module.dev_vpc.public_subnet_ids
  security_group_id = module.dev_sg.public_alb_sg_id
  type              = "public"
  services = {
    combined = {
      port              = 8000
      health_check_path = "/health"
      priority          = 100
      path_patterns     = ["/api/*"]
    }
    admin = {
      port              = 8000
      health_check_path = "/health"
      priority          = 200
      path_patterns     = ["/admin", "/admin/*"]
    }
  }
}

module "dev_rds" {
  source                  = "./modules/rds"
  environment             = "dev"
  vpc_id                  = module.dev_vpc.vpc_id
  subnet_ids              = module.dev_vpc.private_data_subnet_ids
  security_group_id       = module.dev_sg.rds_sg_id
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  multi_az                = false
  backup_retention_period = 0
  deletion_protection     = false
}

module "dev_elasticache" {
  source            = "./modules/elasticache"
  environment       = "dev"
  subnet_ids        = module.dev_vpc.private_data_subnet_ids
  security_group_id = module.dev_sg.elasticache_sg_id
  node_type         = "cache.t3.micro"
}

module "dev_bastion" {
  source            = "./modules/bastion"
  environment       = "dev"
  vpc_id            = module.dev_vpc.vpc_id
  subnet_id         = module.dev_vpc.public_subnet_ids[0]
  security_group_id = module.dev_sg.bastion_sg_id
  key_pair_name     = "${var.bastion_key_name}-dev"
  public_key        = var.bastion_public_key
}

module "dev_ssm" {
  source                     = "./modules/ssm"
  environment                = "dev"
  rds_endpoint               = module.dev_rds.endpoint
  rds_port                   = module.dev_rds.port
  rds_db_name                = module.dev_rds.db_name
  rds_username               = module.dev_rds.master_username
  rds_password               = module.dev_rds.master_password
  redis_endpoint             = module.dev_elasticache.endpoint
  redis_port                 = module.dev_elasticache.port
  sqs_queue_url              = ""
  s3_invoice_bucket          = ""
  cognito_customer_pool_id   = module.cognito.customer_pool_id
  cognito_customer_client_id = module.cognito.customer_client_id
  cognito_admin_pool_id      = module.cognito.admin_pool_id
  cognito_admin_client_id    = module.cognito.admin_client_id
}

module "dev_ecs" {
  source       = "./modules/ecs"
  environment  = "dev"
  vpc_id       = module.dev_vpc.vpc_id
  subnet_ids   = module.dev_vpc.private_app_subnet_ids
  cluster_name = "shopcloud-dev"
  ecr_urls     = module.ecr.repository_urls

  services = {
    combined = {
      cpu               = 256
      memory            = 512
      desired_count     = 1
      container_port    = 8000
      security_group_id = module.dev_sg.customer_fargate_sg_id
      target_group_arn  = module.dev_alb.target_group_arns["combined"]
    }
    admin = {
      cpu               = 256
      memory            = 512
      desired_count     = 1
      container_port    = 8000
      security_group_id = module.dev_sg.admin_fargate_sg_id
      target_group_arn  = module.dev_alb.target_group_arns["admin"]
    }
  }

  standalone_tasks = {
    migrate = {
      cpu    = 256
      memory = 512
    }
  }

  ssm_parameter_arns = module.dev_ssm.parameter_arns

  ssm_secrets = {
    DATABASE_URL            = module.dev_ssm.database_url_arn
    REDIS_URL               = module.dev_ssm.redis_url_arn
    SQS_QUEUE_URL           = module.dev_ssm.sqs_queue_url_arn
    S3_INVOICE_BUCKET       = module.dev_ssm.s3_invoice_bucket_arn
    COGNITO_USER_POOL_ID    = module.dev_ssm.cognito_customer_pool_id_arn
    COGNITO_APP_CLIENT_ID   = module.dev_ssm.cognito_customer_client_id_arn
    COGNITO_ADMIN_POOL_ID   = module.dev_ssm.cognito_admin_pool_id_arn
    COGNITO_ADMIN_CLIENT_ID = module.dev_ssm.cognito_admin_client_id_arn
  }
}

# ══════════════════════════════════════════════════════════════
# PHASE 3 — MONITORING & OBSERVABILITY
# ══════════════════════════════════════════════════════════════
# One monitoring module per environment. Prod also wires Lambda + SQS DLQ
# alarms (dev has no invoice pipeline). DLQ name is derived from the queue
# URL: split on / and take the last segment.

module "prod_monitoring" {
  source      = "./modules/monitoring"
  environment = "prod"
  alarm_email = var.alarm_email

  ecs_cluster_name = module.prod_ecs.ecs_cluster_name
  ecs_services = {
    catalog  = "shopcloud-prod-catalog"
    cart     = "shopcloud-prod-cart"
    checkout = "shopcloud-prod-checkout"
    admin    = "shopcloud-prod-admin"
  }

  alb_arn_suffix                = module.prod_public_alb.alb_arn_suffix
  alb_target_group_arn_suffixes = module.prod_public_alb.target_group_arn_suffixes

  rds_instance_id = module.prod_rds.db_instance_id
  rds_has_replica = true

  elasticache_cluster_id = "shopcloud-prod"

  lambda_function_name = "shopcloud-prod-invoice"
  sqs_dlq_name         = element(split("/", module.prod_invoice.sqs_dlq_url), length(split("/", module.prod_invoice.sqs_dlq_url)) - 1)

  nat_gateway_id = module.prod_vpc.nat_gateway_id
}

module "dev_monitoring" {
  source      = "./modules/monitoring"
  environment = "dev"
  alarm_email = "" # dev re-uses prod's email path; skip subscription to avoid double pages

  ecs_cluster_name = module.dev_ecs.ecs_cluster_name
  ecs_services = {
    combined = "shopcloud-dev-combined"
    admin    = "shopcloud-dev-admin"
  }

  alb_arn_suffix                = module.dev_alb.alb_arn_suffix
  alb_target_group_arn_suffixes = module.dev_alb.target_group_arn_suffixes

  rds_instance_id = module.dev_rds.db_instance_id
  rds_has_replica = false

  elasticache_cluster_id = "shopcloud-dev"

  nat_gateway_id = module.dev_vpc.nat_gateway_id
}

# ══════════════════════════════════════════════════════════════
# PHASE 3 — SECURITY HARDENING
# ══════════════════════════════════════════════════════════════
# Per-env: VPC Flow Logs + 3 NACLs. Account-wide singletons (CloudTrail,
# GuardDuty, IAM Access Analyzer, AWS Config) live on prod only.

module "prod_security" {
  source      = "./modules/security_hardening"
  environment = "prod"

  vpc_id                    = module.prod_vpc.vpc_id
  public_subnet_ids         = module.prod_vpc.public_subnet_ids
  private_app_subnet_ids    = module.prod_vpc.private_app_subnet_ids
  private_data_subnet_ids   = module.prod_vpc.private_data_subnet_ids
  public_subnet_cidrs       = module.prod_vpc.public_subnet_cidrs
  private_app_subnet_cidrs  = module.prod_vpc.private_app_subnet_cidrs
  private_data_subnet_cidrs = module.prod_vpc.private_data_subnet_cidrs
  admin_cidr_blocks         = var.admin_cidr_blocks

  waf_acl_arn               = module.edge.waf_acl_arn
  create_account_singletons = true
  alarms_sns_topic_arn      = module.prod_monitoring.sns_topic_arn
  enable_guardduty          = var.enable_guardduty
}

module "dev_security" {
  source      = "./modules/security_hardening"
  environment = "dev"

  vpc_id                    = module.dev_vpc.vpc_id
  public_subnet_ids         = module.dev_vpc.public_subnet_ids
  private_app_subnet_ids    = module.dev_vpc.private_app_subnet_ids
  private_data_subnet_ids   = module.dev_vpc.private_data_subnet_ids
  public_subnet_cidrs       = module.dev_vpc.public_subnet_cidrs
  private_app_subnet_cidrs  = module.dev_vpc.private_app_subnet_cidrs
  private_data_subnet_cidrs = module.dev_vpc.private_data_subnet_cidrs
  admin_cidr_blocks         = var.admin_cidr_blocks
  # No WAF in dev, no account singletons.
}
