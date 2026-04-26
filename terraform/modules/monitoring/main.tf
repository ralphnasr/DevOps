# SNS topic for alarm notifications.
# Every alarm in alarms.tf sends to this topic; the email subscription is
# created only when var.alarm_email is non-empty (skipped for dev to avoid
# noise — devs get notified through the prod topic anyway).

resource "aws_sns_topic" "alarms" {
  name = "shopcloud-${var.environment}-alarms"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}
