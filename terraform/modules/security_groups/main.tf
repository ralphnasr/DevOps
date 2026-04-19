# ── Public ALB ──

resource "aws_security_group" "public_alb" {
  name_prefix = "shopcloud-${var.environment}-pub-alb-"
  vpc_id      = var.vpc_id
  description = "Public ALB - HTTP/HTTPS from internet"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "shopcloud-${var.environment}-pub-alb-sg" }

  lifecycle { create_before_destroy = true }
}

# ── Customer Fargate ──

resource "aws_security_group" "customer_fargate" {
  name_prefix = "shopcloud-${var.environment}-cust-fg-"
  vpc_id      = var.vpc_id
  description = "Customer Fargate tasks"

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.public_alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "shopcloud-${var.environment}-cust-fargate-sg" }

  lifecycle { create_before_destroy = true }
}

# ── Internal ALB ──

resource "aws_security_group" "internal_alb" {
  name_prefix = "shopcloud-${var.environment}-int-alb-"
  vpc_id      = var.vpc_id
  description = "Internal ALB - from bastion only"

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "shopcloud-${var.environment}-int-alb-sg" }

  lifecycle { create_before_destroy = true }
}

# ── Admin Fargate ──

resource "aws_security_group" "admin_fargate" {
  name_prefix = "shopcloud-${var.environment}-admin-fg-"
  vpc_id      = var.vpc_id
  description = "Admin Fargate tasks"

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.internal_alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "shopcloud-${var.environment}-admin-fargate-sg" }

  lifecycle { create_before_destroy = true }
}

# ── Bastion ──

resource "aws_security_group" "bastion" {
  name_prefix = "shopcloud-${var.environment}-bastion-"
  vpc_id      = var.vpc_id
  description = "Bastion host - SSH from admin IPs"

  dynamic "ingress" {
    for_each = length(var.admin_cidr_blocks) > 0 ? [1] : []
    content {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = var.admin_cidr_blocks
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "shopcloud-${var.environment}-bastion-sg" }

  lifecycle { create_before_destroy = true }
}

# ── RDS ──

resource "aws_security_group" "rds" {
  name_prefix = "shopcloud-${var.environment}-rds-"
  vpc_id      = var.vpc_id
  description = "RDS PostgreSQL"

  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    security_groups = [
      aws_security_group.customer_fargate.id,
      aws_security_group.admin_fargate.id,
      aws_security_group.lambda.id,
    ]
  }

  tags = { Name = "shopcloud-${var.environment}-rds-sg" }

  lifecycle { create_before_destroy = true }
}

# ── ElastiCache ──

resource "aws_security_group" "elasticache" {
  name_prefix = "shopcloud-${var.environment}-redis-"
  vpc_id      = var.vpc_id
  description = "ElastiCache Redis"

  ingress {
    from_port = 6379
    to_port   = 6379
    protocol  = "tcp"
    security_groups = [
      aws_security_group.customer_fargate.id,
      aws_security_group.admin_fargate.id,
    ]
  }

  tags = { Name = "shopcloud-${var.environment}-redis-sg" }

  lifecycle { create_before_destroy = true }
}

# ── Lambda ──

resource "aws_security_group" "lambda" {
  name_prefix = "shopcloud-${var.environment}-lambda-"
  vpc_id      = var.vpc_id
  description = "Lambda function"

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "RDS access"
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SES/S3 API access"
  }

  tags = { Name = "shopcloud-${var.environment}-lambda-sg" }

  lifecycle { create_before_destroy = true }
}
