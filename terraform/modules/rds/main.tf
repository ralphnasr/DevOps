resource "random_password" "master" {
  length  = 16
  special = false
}

resource "aws_db_subnet_group" "main" {
  name       = "shopcloud-${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = { Name = "shopcloud-${var.environment}-db-subnet" }
}

resource "aws_db_parameter_group" "main" {
  name_prefix = "shopcloud-${var.environment}-pg16-"
  family      = "postgres16"

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = { Name = "shopcloud-${var.environment}-pg16" }

  lifecycle { create_before_destroy = true }
}

resource "aws_db_instance" "main" {
  identifier     = "shopcloud-${var.environment}"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage
  storage_type      = "gp3"
  storage_encrypted = true

  db_name  = var.db_name
  username = var.master_username
  password = random_password.master.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  parameter_group_name   = aws_db_parameter_group.main.name

  multi_az                     = var.multi_az
  publicly_accessible          = false
  backup_retention_period      = var.backup_retention_period
  deletion_protection          = var.deletion_protection
  skip_final_snapshot          = true
  apply_immediately            = true
  performance_insights_enabled = false

  tags = { Name = "shopcloud-${var.environment}-rds" }
}
