# S3 Bucket for PDF Reports
resource "aws_s3_bucket" "c14-bandcamp-reports" {
  bucket        = var.s3_bucket_name
  acl           = "private"

  tags = {
    Name        = var.s3_bucket_name
    Environment = "Production"
  }
}

# Define IAM role for report generation Lambda
resource "aws_iam_role" "c14-bandcamp-reports-lambda-role" {
  name = "c14-bandcamp-reports-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sts:AssumeRole"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach policy to IAM role for report generation Lambda
resource "aws_iam_policy" "c14-bandcamp-reports-policy" {
  name   = "c14-bandcamp-reports-policy"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "ses:SendEmail",
          "ses:SendRawEmail",
          "rds-db:connect",
          "logs:*"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      }
    ]
  })
}

# Attach Policy to IAM Role
resource "aws_iam_role_policy_attachment" "c14-bandcamp-reports-policy-attachment" {
  role       = aws_iam_role.c14-bandcamp-reports-lambda-role.name
  policy_arn = aws_iam_policy.c14-bandcamp-reports-policy.arn
}

# Define Lambda function for report generation
resource "aws_lambda_function" "c14-bandcamp-reports-lambda-function" {
  function_name = "c14-bandcamp-reports-lambda"
  role          = aws_iam_role.c14-bandcamp-reports-lambda-role.arn
  package_type  = "Image"
  image_uri     = "INSERT ECR IMAGE URI HERE"
  timeout       = 900
  memory_size   = 512
  environment {
    variables = {
      DB_USER         = var.db_user
      DB_PASSWORD     = var.db_password
      DB_NAME         = var.db_name
      DB_HOST         = var.db_host
      DB_PORT         = var.db_port
      S3_BUCKET       = var.s3_bucket_name
      SENDER_EMAIL    = var.sender_email
      RECIPIENT_EMAIL = var.recipient_email
    }
  }
}

# Define cloudwatch rule for daily scheduling at 9:00 AM 
resource "aws_cloudwatch_event_rule" "c14-bandcamp-reports-rule" {
  name                = "c14-bandcamp-reports-rule"
  description         = "Trigger the reports Lambda every day at 9:00 AM UTC"
  schedule_expression = "cron(0 9 * * ? *)"
}

# EventBridge target for Lambda
resource "aws_cloudwatch_event_target" "c14-bandcamp-reports-target" {
  rule      = aws_cloudwatch_event_rule.c14-bandcamp-reports-rule.name
  arn       = aws_lambda_function.c14-bandcamp-reports-lambda-function.arn
}

# Add Lambda permissions to allow EventBridge to invoke it
resource "aws_lambda_permission" "c14-bandcamp-reports-lambda-permission" {
  statement_id  = "AllowEventBridgeInvokeReports"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  function_name = aws_lambda_function.c14-bandcamp-reports-lambda-function.function_name
  source_arn    = aws_cloudwatch_event_rule.c14-bandcamp-reports-rule.arn
}
