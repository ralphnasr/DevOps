# Cross-region RDS read replica for DR + low-latency EU reads.
# Per Phase 1 report §2.3 and §5.3: eu-west-1 (Ireland) replica of us-east-1 primary.
#
# Provider must be passed in from root as `providers = { aws = aws.eu_west_1 }`.
# Source DB must be in the `available` state (not stopped) before `terraform apply`.

terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      configuration_aliases = [aws]
    }
  }
}

data "aws_availability_zones" "dr" {
  state = "available"
}

resource "aws_vpc" "dr" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "shopcloud-dr-vpc" }
}

resource "aws_subnet" "dr" {
  count             = 2
  vpc_id            = aws_vpc.dr.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.dr.names[count.index]

  tags = { Name = "shopcloud-dr-subnet-${count.index}" }
}

resource "aws_db_subnet_group" "dr" {
  name       = "shopcloud-dr-db-subnet"
  subnet_ids = aws_subnet.dr[*].id

  tags = { Name = "shopcloud-dr-db-subnet" }
}

resource "aws_security_group" "dr" {
  name        = "shopcloud-dr-rds-sg"
  description = "Cross-region RDS replica — VPC-internal access only"
  vpc_id      = aws_vpc.dr.id

  ingress {
    description = "Postgres from within DR VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.dr.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "shopcloud-dr-rds-sg" }
}

resource "aws_db_instance" "replica" {
  identifier          = "shopcloud-prod-dr"
  replicate_source_db = var.source_db_arn
  instance_class      = var.instance_class

  db_subnet_group_name   = aws_db_subnet_group.dr.name
  vpc_security_group_ids = [aws_security_group.dr.id]

  publicly_accessible        = false
  storage_encrypted          = true
  auto_minor_version_upgrade = true
  skip_final_snapshot        = true
  apply_immediately          = true
  backup_retention_period    = 0

  tags = { Name = "shopcloud-prod-dr-replica" }
}
