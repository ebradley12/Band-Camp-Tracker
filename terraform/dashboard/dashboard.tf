# Security group for Application Load Balancer (ALB)
resource "aws_security_group" "c14_bandcamp_alb_sg" {
  name_prefix = "c14-bandcamp-alb-sg-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "c14-bandcamp-alb-sg"
  }
}

# Create the Application Load Balancer (ALB)
resource "aws_lb" "c14_bandcamp_dashboard_alb" {
  name                 = "c14-bandcamp-dashboard-alb"
  internal             = false
  load_balancer_type   = "application"
  security_groups      = [aws_security_group.c14_bandcamp_alb_sg.id]
  subnets              = var.subnet_ids
  enable_deletion_protection = false

  tags = {
    Name = "c14-bandcamp-dashboard-alb"
  }
}

# Create the Application Load Balancer Listener
resource "aws_lb_listener" "c14_bandcamp_http_listener" {
  load_balancer_arn = aws_lb.c14_bandcamp_dashboard_alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.c14_bandcamp_dashboard_target_group.arn
  }
}

# Create the target group for the ECS service
resource "aws_lb_target_group" "c14_bandcamp_dashboard_target_group" {
  name        = "c14-bandcamp-dashboard-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"
}

# Create the security group for the ECS task
resource "aws_security_group" "c14_bandcamp_dashboard_ecs_sg" {
  name_prefix = "c14-bandcamp-dashboard-ecs-sg-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
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

# Create the IAM role for ECS task execution
resource "aws_iam_role" "ecs_task_execution" {
  name = "ecsTaskExecutionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project     = "c14-bandcamp-dashboard"
    Environment = "production"
  }
}

# Attach the managed policy to the IAM role
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Create the ECS task definition
resource "aws_ecs_task_definition" "c14_bandcamp_dashboard_task" {
  family                   = "c14-bandcamp-dashboard-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name      = "c14-bandcamp-dashboard-container"
    image     = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/c14-bandcamp-dashboard-ecr:latest"
    cpu       = 256
    memory    = 512
    essential = true
    portMappings = [{
      containerPort = 80
      hostPort      = 80
      protocol      = "tcp"
    }]
  }])
}

# Create the ECS service
resource "aws_ecs_service" "c14_bandcamp_dashboard_service" {
  name            = "c14-bandcamp-dashboard-service"
  cluster         = var.ecs_cluster_name  # Use the preexisting cluster name
  task_definition = aws_ecs_task_definition.c14_bandcamp_dashboard_task.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.c14_bandcamp_dashboard_ecs_sg.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.c14_bandcamp_dashboard_target_group.arn
    container_name   = "c14-bandcamp-dashboard-container"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.c14_bandcamp_http_listener]
}

