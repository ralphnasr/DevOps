resource "aws_elasticache_subnet_group" "main" {
  name       = "shopcloud-${var.environment}-redis"
  subnet_ids = var.subnet_ids

  tags = { Name = "shopcloud-${var.environment}-redis-subnet" }
}

resource "aws_elasticache_parameter_group" "main" {
  name   = "shopcloud-${var.environment}-redis7"
  family = "redis7"

  tags = { Name = "shopcloud-${var.environment}-redis7" }
}

resource "aws_elasticache_cluster" "main" {
  cluster_id           = "shopcloud-${var.environment}"
  engine               = "redis"
  engine_version       = "7.0"
  node_type            = var.node_type
  num_cache_nodes      = 1
  port                 = 6379
  parameter_group_name = aws_elasticache_parameter_group.main.name
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [var.security_group_id]

  tags = { Name = "shopcloud-${var.environment}-redis" }
}
