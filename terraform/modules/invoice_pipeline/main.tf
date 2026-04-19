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

# ── Lambda IAM Role ──

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

# ── Lambda Function ──
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
    }
  }

  tags = { Name = "shopcloud-${var.environment}-invoice" }
}

# ── SQS → Lambda Trigger ──

resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.orders.arn
  function_name    = aws_lambda_function.invoice.arn
  batch_size       = 1
}

# ── Data Sources ──

data "aws_caller_identity" "current" {}
