# ── SQS Queues ──

resource "aws_sqs_queue" "dlq" {
  name                      = "shopcloud-${var.environment}-orders-dlq"
  message_retention_seconds = 1209600 # 14 days

  tags = { Name = "shopcloud-${var.environment}-orders-dlq" }
}

resource "aws_sqs_queue" "orders" {
  name                       = "shopcloud-${var.environment}-orders"
  visibility_timeout_seconds = 60
  message_retention_seconds  = 345600 # 4 days

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 4
  })

  tags = { Name = "shopcloud-${var.environment}-orders" }
}

# ── S3 Bucket ──

resource "aws_s3_bucket" "invoices" {
  bucket        = "shopcloud-${var.environment}-invoices-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = { Name = "shopcloud-${var.environment}-invoices" }
}

resource "aws_s3_bucket_versioning" "invoices" {
  bucket = aws_s3_bucket.invoices.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_lifecycle_configuration" "invoices" {
  bucket = aws_s3_bucket.invoices.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    filter {}

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }
}

# ── SES ──

resource "aws_ses_email_identity" "sender" {
  email = var.ses_verified_email
}

# Configuration set — named bundle of sending policies.
# Wires every SendEmail call that references this set into the SNS event stream
# below, so bounces/complaints reach the auto-suppression Lambda.
resource "aws_ses_configuration_set" "main" {
  name                       = "shopcloud-${var.environment}-invoice"
  reputation_metrics_enabled = true

  delivery_options {
    tls_policy = "Require"
  }
}

# SNS topic that receives every bounce / complaint / reject / delivery event
# for mails sent with the configuration set above.
resource "aws_sns_topic" "ses_events" {
  name = "shopcloud-${var.environment}-ses-events"

  tags = { Name = "shopcloud-${var.environment}-ses-events" }
}

resource "aws_ses_event_destination" "sns" {
  name                   = "bounce-complaint-reject-delivery"
  configuration_set_name = aws_ses_configuration_set.main.name
  enabled                = true
  matching_types         = ["bounce", "complaint", "reject", "delivery"]

  sns_destination {
    topic_arn = aws_sns_topic.ses_events.arn
  }
}

# Allow SES to publish to the SNS topic.
data "aws_iam_policy_document" "sns_ses_publish" {
  statement {
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.ses_events.arn]

    principals {
      type        = "Service"
      identifiers = ["ses.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "ses_events" {
  arn    = aws_sns_topic.ses_events.arn
  policy = data.aws_iam_policy_document.sns_ses_publish.json
}

# ── Invoice Lambda IAM Role ──

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name_prefix        = "shopcloud-${var.environment}-invoice-"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy" "lambda" {
  name = "invoice-permissions"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = aws_sqs_queue.orders.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject"]
        Resource = "${aws_s3_bucket.invoices.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

# ── Invoice Lambda ──
#
# Native deps (psycopg2-binary, fpdf2 → Pillow) ship as Linux x86_64 wheels,
# so we install them inside a Lambda-compatible Docker image into app/invoice/build/
# and zip THAT directory. Zipping app/invoice/ directly (without the install step)
# yields a 7 KB bundle that crashes at cold start with `No module named psycopg2`.

resource "null_resource" "lambda_build" {
  triggers = {
    source_hash       = filesha256("${path.module}/../../../app/invoice/lambda_function.py")
    requirements_hash = filesha256("${path.module}/../../../app/invoice/requirements.txt")
  }

  # Runs on Linux CI via the default sh interpreter. For local Windows applies,
  # pre-build the zip with `bash scripts/build_lambdas.sh` from Git Bash; this
  # null_resource will then be a no-op because state will already match.
  provisioner "local-exec" {
    working_dir = "${path.module}/../../../app/invoice"
    command     = <<-EOT
      rm -rf build && mkdir build && cp lambda_function.py build/ && \
      docker run --rm --platform linux/amd64 \
        -v "$(pwd)/build":/var/task \
        -v "$(pwd)/requirements.txt":/var/task/requirements.txt \
        --entrypoint /bin/bash \
        public.ecr.aws/sam/build-python3.12 \
        -c "pip install -r /var/task/requirements.txt -t /var/task --no-cache-dir"
    EOT
  }
}

data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../app/invoice/build"
  output_path = "${path.module}/lambda.zip"

  depends_on = [null_resource.lambda_build]
}

resource "aws_lambda_function" "invoice" {
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  function_name    = "shopcloud-${var.environment}-invoice"
  role             = aws_iam_role.lambda.arn
  handler          = "lambda_function.handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      S3_INVOICE_BUCKET = aws_s3_bucket.invoices.id
      DB_HOST           = var.rds_endpoint
      DB_NAME           = var.rds_db_name
      DB_USER           = var.rds_username
      DB_PASSWORD       = var.rds_password
      SES_SENDER_EMAIL  = var.ses_verified_email
      SES_CONFIG_SET    = aws_ses_configuration_set.main.name
    }
  }

  tags = { Name = "shopcloud-${var.environment}-invoice" }
}

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.orders.arn
  function_name    = aws_lambda_function.invoice.arn
  batch_size       = 1
}

# ══════════════════════════════════════════════════════════════════════
# Bounce/Complaint Auto-Suppression Lambda
# ══════════════════════════════════════════════════════════════════════
# SES → SNS → this Lambda. On hard bounce we mark the customer's email as
# suppressed in RDS so checkout stops publishing invoice messages for them.
# Keeps us below AWS's 5% bounce / 0.1% complaint enforcement thresholds.

resource "null_resource" "bounce_lambda_build" {
  triggers = {
    source_hash = filesha256("${path.module}/../../../app/invoice/bounce_handler.py")
    # Force rebuild on every plan/apply so `data.archive_file.bounce_lambda`
    # below always defers to apply time. Without this, CI plan tries to read
    # bounce_build/ at plan time and fails because the dir was only created
    # by a prior local apply on the developer's box.
    always_run = timestamp()
  }

  provisioner "local-exec" {
    working_dir = "${path.module}/../../../app/invoice"
    command     = <<-EOT
      rm -rf bounce_build && mkdir bounce_build && cp bounce_handler.py bounce_build/ && \
      docker run --rm --platform linux/amd64 \
        -v "$(pwd)/bounce_build":/var/task \
        --entrypoint /bin/bash \
        public.ecr.aws/sam/build-python3.12 \
        -c "pip install psycopg2-binary==2.9.10 -t /var/task --no-cache-dir"
    EOT
  }
}

data "archive_file" "bounce_lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../../../app/invoice/bounce_build"
  output_path = "${path.module}/bounce_lambda.zip"

  depends_on = [null_resource.bounce_lambda_build]
}

resource "aws_iam_role" "bounce_lambda" {
  name_prefix        = "shopcloud-${var.environment}-bounce-"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy" "bounce_lambda" {
  name = "bounce-handler-permissions"
  role = aws_iam_role.bounce_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "bounce_handler" {
  filename         = data.archive_file.bounce_lambda.output_path
  source_code_hash = data.archive_file.bounce_lambda.output_base64sha256
  function_name    = "shopcloud-${var.environment}-bounce-handler"
  role             = aws_iam_role.bounce_lambda.arn
  handler          = "bounce_handler.handler"
  runtime          = "python3.12"
  timeout          = 15
  memory_size      = 128

  vpc_config {
    subnet_ids         = var.subnet_ids
    security_group_ids = [var.security_group_id]
  }

  environment {
    variables = {
      DB_HOST     = var.rds_endpoint
      DB_NAME     = var.rds_db_name
      DB_USER     = var.rds_username
      DB_PASSWORD = var.rds_password
    }
  }

  tags = { Name = "shopcloud-${var.environment}-bounce-handler" }
}

resource "aws_sns_topic_subscription" "bounce_handler" {
  topic_arn = aws_sns_topic.ses_events.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.bounce_handler.arn
}

resource "aws_lambda_permission" "bounce_sns" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.bounce_handler.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.ses_events.arn
}

# ══════════════════════════════════════════════════════════════════════
# CloudWatch Dashboard + Alarms (sender reputation)
# ══════════════════════════════════════════════════════════════════════
# Alarms fire at the exact thresholds AWS uses to place accounts under review:
#   - 5% bounce rate    → enforcement warning
#   - 0.1% complaint rate → enforcement warning
# Owning these alarms ourselves means we react before AWS does.

resource "aws_cloudwatch_dashboard" "ses" {
  dashboard_name = "shopcloud-${var.environment}-ses"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Send / Delivery / Bounce / Complaint"
          region  = "us-east-1"
          view    = "timeSeries"
          stacked = false
          metrics = [
            ["AWS/SES", "Send"],
            [".", "Delivery"],
            [".", "Bounce"],
            [".", "Complaint"],
            [".", "Reject"]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Reputation — Bounce Rate (alarm at 5%)"
          region  = "us-east-1"
          view    = "timeSeries"
          metrics = [["AWS/SES", "Reputation.BounceRate"]]
          yAxis   = { left = { min = 0, max = 0.10 } }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "Reputation — Complaint Rate (alarm at 0.1%)"
          region  = "us-east-1"
          view    = "timeSeries"
          metrics = [["AWS/SES", "Reputation.ComplaintRate"]]
          yAxis   = { left = { min = 0, max = 0.005 } }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Invoice Lambda — invocations / errors / throttles"
          region = "us-east-1"
          view   = "timeSeries"
          metrics = [
            ["AWS/Lambda", "Invocations", "FunctionName", aws_lambda_function.invoice.function_name],
            [".", "Errors", ".", "."],
            [".", "Throttles", ".", "."]
          ]
        }
      }
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "bounce_rate" {
  alarm_name          = "shopcloud-${var.environment}-ses-bounce-rate-high"
  alarm_description   = "SES bounce rate above AWS's 5% enforcement threshold"
  namespace           = "AWS/SES"
  metric_name         = "Reputation.BounceRate"
  statistic           = "Average"
  period              = 900
  evaluation_periods  = 1
  threshold           = 0.05
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.ses_events.arn]
}

resource "aws_cloudwatch_metric_alarm" "complaint_rate" {
  alarm_name          = "shopcloud-${var.environment}-ses-complaint-rate-high"
  alarm_description   = "SES complaint rate above AWS's 0.1% enforcement threshold"
  namespace           = "AWS/SES"
  metric_name         = "Reputation.ComplaintRate"
  statistic           = "Average"
  period              = 900
  evaluation_periods  = 1
  threshold           = 0.001
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.ses_events.arn]
}

resource "aws_cloudwatch_metric_alarm" "dlq_depth" {
  alarm_name          = "shopcloud-${var.environment}-orders-dlq-not-empty"
  alarm_description   = "Invoice messages landing in DLQ after 4 retries — usually a permanent SES reject or a malformed payload. Each one is a customer who did not get their invoice email."
  namespace           = "AWS/SQS"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  dimensions          = { QueueName = aws_sqs_queue.dlq.name }
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.ses_events.arn]
}

# ── Data Sources ──

data "aws_caller_identity" "current" {}
