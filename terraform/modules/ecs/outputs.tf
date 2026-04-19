output "ecs_cluster_name" {
  value = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  value = aws_ecs_cluster.main.arn
}

output "task_definition_arns" {
  value = { for k, v in aws_ecs_task_definition.services : k => v.arn }
}

output "standalone_task_definition_arns" {
  value = { for k, v in aws_ecs_task_definition.standalone : k => v.arn }
}

output "service_arns" {
  value = { for k, v in aws_ecs_service.services : k => v.id }
}
