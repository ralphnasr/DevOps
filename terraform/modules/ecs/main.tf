# ── Cluster ──

resource "aws_ecs_cluster" "main" {
  name = var.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = { Name = var.cluster_name }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE"]

  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight            = 1
  }
}

# ── IAM Roles ──

data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "execution" {
  name_prefix        = "shopcloud-${var.environment}-exec-"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "execution_ecr" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "execution_ssm" {
  name = "ssm-read"
  role = aws_iam_role.execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameters", "ssm:GetParameter"]
        Resource = var.ssm_parameter_arns
      }
    ]
  })
}

resource "aws_iam_role" "task" {
  name_prefix        = "shopcloud-${var.environment}-task-"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy" "task_permissions" {
  name = "task-permissions"
  role = aws_iam_role.task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = var.sqs_queue_arn != "" ? var.sqs_queue_arn : "arn:aws:sqs:*:*:shopcloud-*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = var.s3_bucket_arn != "" ? "${var.s3_bucket_arn}/*" : "arn:aws:s3:::shopcloud-*/*"
      }
    ]
  })
}

# ── Log Groups ──

resource "aws_cloudwatch_log_group" "services" {
  for_each          = var.services
  name              = "/ecs/shopcloud-${var.environment}/${each.key}"
  retention_in_days = 30

  tags = { Name = "shopcloud-${var.environment}-${each.key}" }
}

resource "aws_cloudwatch_log_group" "standalone" {
  for_each          = var.standalone_tasks
  name              = "/ecs/shopcloud-${var.environment}/${each.key}"
  retention_in_days = 30

  tags = { Name = "shopcloud-${var.environment}-${each.key}" }
}

# ── Task Definitions ──

resource "aws_ecs_task_definition" "services" {
  for_each = var.services

  family                   = "shopcloud-${var.environment}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name  = each.key
      image = "${lookup(var.ecr_urls, each.key, var.ecr_urls["catalog"])}:latest"
      portMappings = [
        {
          containerPort = each.value.container_port
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "ENVIRONMENT", value = var.environment }
      ]
      secrets = [
        for env_name, ssm_arn in var.ssm_secrets : {
          name      = env_name
          valueFrom = ssm_arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.services[each.key].name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = each.key
        }
      }
      essential = true
    }
  ])

  tags = { Name = "shopcloud-${var.environment}-${each.key}" }
}

data "aws_region" "current" {}

# ── Standalone task definitions (no service) ──
# Used for one-off jobs like DB migrations that run via `aws ecs run-task`.
# Image comes from the matching ECR repo (so var.ecr_urls must include the key).

resource "aws_ecs_task_definition" "standalone" {
  for_each = var.standalone_tasks

  family                   = "shopcloud-${var.environment}-${each.key}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = each.value.cpu
  memory                   = each.value.memory
  execution_role_arn       = aws_iam_role.execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name  = each.key
      image = "${lookup(var.ecr_urls, each.key, var.ecr_urls["catalog"])}:latest"
      environment = [
        { name = "ENVIRONMENT", value = var.environment }
      ]
      secrets = [
        for env_name, ssm_arn in var.ssm_secrets : {
          name      = env_name
          valueFrom = ssm_arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.standalone[each.key].name
          "awslogs-region"        = data.aws_region.current.name
          "awslogs-stream-prefix" = each.key
        }
      }
      essential = true
    }
  ])

  tags = { Name = "shopcloud-${var.environment}-${each.key}" }
}

# ── Services ──

resource "aws_ecs_service" "services" {
  for_each = var.services

  name            = each.key
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.services[each.key].arn
  desired_count   = each.value.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [each.value.security_group_id]
  }

  load_balancer {
    target_group_arn = each.value.target_group_arn
    container_name   = each.key
    container_port   = each.value.container_port
  }

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  tags = { Name = "shopcloud-${var.environment}-${each.key}" }
}

# ── Auto Scaling ──

resource "aws_appautoscaling_target" "services" {
  for_each = var.services

  max_capacity       = 4
  min_capacity       = each.value.desired_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${each.key}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  depends_on = [aws_ecs_service.services]
}

resource "aws_appautoscaling_policy" "cpu" {
  for_each = var.services

  name               = "shopcloud-${var.environment}-${each.key}-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.services[each.key].resource_id
  scalable_dimension = aws_appautoscaling_target.services[each.key].scalable_dimension
  service_namespace  = aws_appautoscaling_target.services[each.key].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 70.0
  }
}
