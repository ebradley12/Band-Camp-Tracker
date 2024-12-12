
# Create the security group for the ECS task
resource "aws_security_group" "c14_bandcamp_dashboard_ecs_sg" {
  name = "c14-bandcamp-dashboard-ecs-sg"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow traffic from the ALB
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "c14-bandcamp-dashboard-ecs-sg"
  }
}


data "aws_iam_role" "ecsTaskExecutionRole" {
  name = "ecsTaskExecutionRole"
}

resource "aws_iam_policy" "bandcamp_ecs_service_policy" {
  name        = "bandcamp_ecs_service_policy"
  description = "Allow ECS service to upload plant data files to the S3 bucket"
  lifecycle {
    prevent_destroy = false
  }
  policy = jsonencode({
    Version : "2012-10-17",
    Statement : [
      {
        Effect   : "Allow",
        Action   : [
          "s3:GetObject"
        ],
        Resource : "arn:aws:s3:::c14-bandcamp-reports/*"
      }
    ]
  })
}

# Attach the managed policy to the IAM role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = data.aws_iam_role.ecsTaskExecutionRole.name
  policy_arn = aws_iam_policy.bandcamp_ecs_service_policy.arn
}

# Create the ECS task definition
resource "aws_ecs_task_definition" "c14_bandcamp_dashboard_task" {
  family                   = "c14-bandcamp-dashboard-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = data.aws_iam_role.ecsTaskExecutionRole.arn
  task_role_arn            = data.aws_iam_role.ecsTaskExecutionRole.arn

  container_definitions = jsonencode([{
    name      = "c14-bandcamp-dashboard-container"
    image     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c14-bandcamp-dashboard-ecr:latest"
    cpu       = 256
    memory    = 512
    essential = true
    portMappings = [{
      containerPort = 8501
      hostPort      = 8501
      protocol      = "tcp"
    }]
    environment = [
      {
        name  = "DB_USER"
        value = var.db_user
      },
      {
        name  = "DB_PASSWORD"
        value = var.db_password
      },
      {
        name  = "DB_HOST"
        value = var.db_host
      },
      {
        name  = "DB_PORT"
        value = var.db_port
      },
      {
        name  = "DB_NAME"
        value = var.db_name
      },
      {
        name  = "S3_bucket"
        value = var.s3_bucket_name
      },
      {
        name  = "S3_folder"
        value = var.s3_folder
      },
      {
        name  = "aws_access_key_id"
        value = var.aws_access_key_id
      },
      {
        name  = "aws_secret_access_key"
        value = var.aws_secret_access_key
      }
    ]
  }])
  runtime_platform {
    cpu_architecture       = "X86_64"
    operating_system_family = "LINUX"
  }
}

# Create the ECS service
resource "aws_ecs_service" "c14_bandcamp_dashboard_service" {
  name            = "c14-bandcamp-dashboard-service"
  cluster         = var.ecs_cluster_name  # Use the preexisting cluster name
  task_definition = aws_ecs_task_definition.c14_bandcamp_dashboard_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.c14_bandcamp_dashboard_ecs_sg.id]
    assign_public_ip = true
  }
}

