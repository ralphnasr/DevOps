# Three NACL tiers — stateless allow-lists that complement (not replace) the
# stateful security groups. SGs already enforce identity-based rules; NACLs
# add a second layer at the subnet boundary so a misconfigured SG doesn't
# silently expose a tier.

# ── Public subnets: HTTP/HTTPS in, SSH from admin CIDRs only ──

resource "aws_network_acl" "public" {
  vpc_id     = var.vpc_id
  subnet_ids = var.public_subnet_ids

  # HTTP / HTTPS from anywhere (CloudFront + ALB)
  ingress {
    rule_no    = 100
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }
  ingress {
    rule_no    = 110
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Bastion SSH — only from whitelisted admin IPs
  dynamic "ingress" {
    for_each = { for idx, cidr in var.admin_cidr_blocks : idx => cidr }
    content {
      rule_no    = 120 + ingress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = ingress.value
      from_port  = 22
      to_port    = 22
    }
  }

  # Ephemeral return ports (responses to outbound connections — NACLs are stateless)
  ingress {
    rule_no    = 200
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # All outbound (ALB → Fargate, bastion → SSM, etc.)
  egress {
    rule_no    = 100
    protocol   = "-1"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = { Name = "shopcloud-${var.environment}-public-nacl" }
}

# ── Private app subnets: Fargate tier ──
# In: traffic from public (ALB → 8000), data tier responses, NAT return.
# Out: to data tier on 5432/6379, internet on 443 (ECR pulls, AWS APIs, SES, SQS).

resource "aws_network_acl" "private_app" {
  vpc_id     = var.vpc_id
  subnet_ids = var.private_app_subnet_ids

  # ALB → Fargate on container port 8000
  dynamic "ingress" {
    for_each = { for idx, cidr in var.public_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 100 + ingress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = ingress.value
      from_port  = 8000
      to_port    = 8000
    }
  }

  # Return traffic from data tier (Postgres / Redis responses)
  dynamic "ingress" {
    for_each = { for idx, cidr in var.private_data_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 200 + ingress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = ingress.value
      from_port  = 1024
      to_port    = 65535
    }
  }

  # Return traffic from internet (via NAT)
  ingress {
    rule_no    = 300
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Outbound to data tier (Postgres)
  dynamic "egress" {
    for_each = { for idx, cidr in var.private_data_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 100 + egress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = egress.value
      from_port  = 5432
      to_port    = 5432
    }
  }

  # Outbound to data tier (Redis)
  dynamic "egress" {
    for_each = { for idx, cidr in var.private_data_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 200 + egress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = egress.value
      from_port  = 6379
      to_port    = 6379
    }
  }

  # Outbound to internet on 443 (AWS APIs + ECR + SES + SQS)
  egress {
    rule_no    = 300
    protocol   = "tcp"
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Ephemeral return to public (ALB ↔ Fargate)
  dynamic "egress" {
    for_each = { for idx, cidr in var.public_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 400 + egress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = egress.value
      from_port  = 1024
      to_port    = 65535
    }
  }

  tags = { Name = "shopcloud-${var.environment}-private-app-nacl" }
}

# ── Private data subnets: RDS + Redis ──
# Strictest tier — only the app subnets can reach DB ports. No internet path
# (also enforced by absence of NAT route in the data route table). NACLs make
# the intent explicit so a route table mistake doesn't open the tier.

resource "aws_network_acl" "private_data" {
  vpc_id     = var.vpc_id
  subnet_ids = var.private_data_subnet_ids

  # Postgres from app subnets only
  dynamic "ingress" {
    for_each = { for idx, cidr in var.private_app_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 100 + ingress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = ingress.value
      from_port  = 5432
      to_port    = 5432
    }
  }

  # Redis from app subnets only
  dynamic "ingress" {
    for_each = { for idx, cidr in var.private_app_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 200 + ingress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = ingress.value
      from_port  = 6379
      to_port    = 6379
    }
  }

  # Ephemeral return only to app subnets
  dynamic "egress" {
    for_each = { for idx, cidr in var.private_app_subnet_cidrs : idx => cidr }
    content {
      rule_no    = 100 + egress.key
      protocol   = "tcp"
      action     = "allow"
      cidr_block = egress.value
      from_port  = 1024
      to_port    = 65535
    }
  }

  tags = { Name = "shopcloud-${var.environment}-private-data-nacl" }
}
