# Define IAM role for the pipeline Lambda
resource "aws_iam_role" "c14-bandcamp-pipeline-lambda-role" {
  name = "c14-bandcamp-pipeline-lambda-role"
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

# Define lambda function for pipeline
resource "aws_lambda_function" "c14-bandcamp-pipeline-lambda-function" {
  function_name = "c14-band-camp-pipeline-lambda"
  role          = aws_iam_role.c14-bandcamp-pipeline-lambda-role.arn
  package_type  = "Image"
  image_uri     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c14-bandcamp-pipeline-ecr@sha256:b34e2cc9c46b2aedc32bb445695dc8c859a2e83d27eb1929b3520fd5875c1b32"
  timeout       = 900 
  memory_size   = 512
  environment {
    variables = {
      DB_USER            = var.db_user
      DB_PASSWORD        = var.db_password
      DB_HOST = var.db_host
      DB_PORT = var.db_port
      DB_NAME = var.db_name
    }
  }
}

# Create cloudwatch event rule - schedule for the event
resource "aws_cloudwatch_event_rule" "c14-bandcamp-pipeline-rule" {
  name                = "c14-bandcamp-pipeline-rule"
  description         = "trigger the pipeline lambda every ten minutes"
  schedule_expression = "cron(0/10 * * * ? *)"
}

# Eventbridge target for lambda
resource "aws_cloudwatch_event_target" "c14-bandcamp-pipeline-target" {
  rule      = aws_cloudwatch_event_rule.c14-bandcamp-pipeline-rule.name
  arn       = aws_lambda_function.c14-bandcamp-pipeline-lambda-function.arn
}

# Lambda permission - allows eventbridge to trigger lambda
resource "aws_lambda_permission" "c14-bandcamp-pipeline-lambda-permission" {
  statement_id  = "AllowEventBridgeInvokeETL"
  action        = "lambda:InvokeFunction"
  principal     = "events.amazonaws.com"
  function_name = aws_lambda_function.c14-bandcamp-pipeline-lambda-function.function_name
  source_arn    = aws_cloudwatch_event_rule.c14-bandcamp-pipeline-rule.arn
}

# Policy to define permissions
resource "aws_iam_policy" "c14-bandcamp-pipeline-policy" {
  name        = "c14-bandcamp-pipeline-policy"
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
resource "aws_iam_role_policy_attachment" "c14-bandcamp-pipeline-policy-attachment" {
  role       = aws_iam_role.c14-bandcamp-pipeline-lambda-role.name
  policy_arn = aws_iam_policy.c14-bandcamp-pipeline-policy.arn
}
