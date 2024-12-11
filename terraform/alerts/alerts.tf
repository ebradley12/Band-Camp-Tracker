# Define IAM role for the alerts Lambda
resource "aws_iam_role" "c14-bandcamp-alerts-lambda-role" {
  name = "c14-bandcamp-alerts-lambda-role"
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

# Define lambda function for alerts
resource "aws_lambda_function" "c14-bandcamp-alerts-lambda-function" {
  function_name = "c14-band-camp-alerts-lambda"
  role          = aws_iam_role.c14-bandcamp-alerts-lambda-role.arn
  package_type  = "Image"
  image_uri     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c14-bandcamp-alerts-ecr@sha256:ad2e2286069f7c15fe4b18b5637de80cb1da2cec3835ffd62a5b920937ac85fa"
  timeout       = 900 
  memory_size   = 512
  environment {
    variables = {
      DB_USER            = var.db_user
      DB_PASSWORD        = var.db_password
      DB_HOST            = var.db_host
      DB_PORT            = var.db_port
      DB_NAME            = var.db_name
    }
  }
}

# Create cloudwatch event rule - schedule for the event
resource "aws_cloudwatch_event_rule" "c14-bandcamp-alerts-rule" {
  name                = "c14-bandcamp-alerts-rule"
  description         = "trigger the alerts lambda every hour"
  schedule_expression = "cron(0 0/1 * * ? *)"
}

# Eventbridge target for lambda
resource "aws_cloudwatch_event_target" "c14-bandcamp-alerts-target" {
  rule      = aws_cloudwatch_event_rule.c14-bandcamp-alerts-rule.name
  arn       = aws_lambda_function.c14-bandcamp-alerts-lambda-function.arn
}

# Lambda permission - allows eventbridge to trigger lambda
resource "aws_lambda_permission" "c14-bandcamp-alerts-lambda-permission" {
  statement_id  = "AllowEventBridgeInvokeAlerts"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  function_name = aws_lambda_function.c14-bandcamp-alerts-lambda-function.function_name
  source_arn    = aws_cloudwatch_event_rule.c14-bandcamp-alerts-rule.arn
}

# Policy to define permissions
resource "aws_iam_policy" "c14-bandcamp-alerts-policy" {
  name        = "c14-bandcamp-alerts-policy"
  policy      = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject", "s3:GetObject", "ecs:RunTask"]
        Resource = "*"
      }
    ]
  })
}

# Attach policy to iam role
resource "aws_iam_role_policy_attachment" "c14-bandcamp-alerts-policy-attachment" {
  role       = aws_iam_role.c14-bandcamp-alerts-lambda-role.name
  policy_arn = aws_iam_policy.c14-bandcamp-alerts-policy.arn
}
