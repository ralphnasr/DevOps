output "replica_endpoint" {
  value = aws_db_instance.replica.address
}

output "replica_arn" {
  value = aws_db_instance.replica.arn
}

output "replica_region" {
  value = "eu-west-1"
}
