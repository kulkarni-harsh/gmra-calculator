data "aws_caller_identity" "current" {}

resource "aws_ecs_cluster" "main" {
  name = "${var.app_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = { Name = "${var.app_name}-cluster" }
}

# --- Backend Task Definition ---

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.app_name}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-backend"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]

      environment = [
        { name = "PROJECT_NAME", value = "MERC" },
        { name = "VERSION", value = "2.0.0" },
        { name = "API_PREFIX", value = "/api" },
        { name = "DEBUG", value = "false" },
        { name = "ALLOWED_ORIGINS", value = "" },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "DYNAMODB_TABLE_NAME", value = aws_dynamodb_table.jobs.name },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.jobs.url },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.reports.bucket },
        { name = "FRONTEND_URL", value = "https://${var.domain_name}" },
      ]

      secrets = [
        { name = "CENSUS_API_KEY",        valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:CENSUS_API_KEY::" },
        { name = "MAPBOX_API_KEY",        valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:MAPBOX_API_KEY::" },
        { name = "ALPHASOPHIA_API_KEY",   valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:ALPHASOPHIA_API_KEY::" },
        { name = "RESEND_API_KEY",        valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:RESEND_API_KEY::" },
        { name = "STRIPE_SECRET_KEY",     valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:STRIPE_SECRET_KEY::" },
        { name = "STRIPE_WEBHOOK_SECRET", valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:STRIPE_WEBHOOK_SECRET::" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.backend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# --- Frontend Task Definition ---

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.app_name}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:${var.frontend_image_tag}"
      essential = true

      portMappings = [
        { containerPort = 80, protocol = "tcp" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.frontend.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# --- Backend ECS Service ---

resource "aws_ecs_service" "backend" {
  name            = "${var.app_name}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "${var.app_name}-backend"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}

# --- Worker Task Definition (same image as backend, different CMD) ---

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.app_name}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "${var.app_name}-worker"
      image     = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
      essential = true

      # Override the default uvicorn CMD — run the SQS consumer instead
      command = ["uv", "run", "python", "-m", "app.worker"]

      environment = [
        { name = "PROJECT_NAME", value = "MERC" },
        { name = "VERSION", value = "2.0.0" },
        { name = "API_PREFIX", value = "/api" },
        { name = "DEBUG", value = "false" },
        { name = "ALLOWED_ORIGINS", value = "" },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "DYNAMODB_TABLE_NAME", value = aws_dynamodb_table.jobs.name },
        { name = "SQS_QUEUE_URL", value = aws_sqs_queue.jobs.url },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.reports.bucket },
      ]

      secrets = [
        { name = "CENSUS_API_KEY",        valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:CENSUS_API_KEY::" },
        { name = "MAPBOX_API_KEY",        valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:MAPBOX_API_KEY::" },
        { name = "ALPHASOPHIA_API_KEY",   valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:ALPHASOPHIA_API_KEY::" },
        { name = "RESEND_API_KEY",        valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:RESEND_API_KEY::" },
        { name = "STRIPE_SECRET_KEY",     valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:STRIPE_SECRET_KEY::" },
        { name = "STRIPE_WEBHOOK_SECRET", valueFrom = "${aws_secretsmanager_secret.api_keys.arn}:STRIPE_WEBHOOK_SECRET::" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.app_name}-worker"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# --- Worker ECS Service ---

resource "aws_ecs_service" "worker" {
  name            = "${var.app_name}-worker"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.backend.id]  # same SG — needs outbound internet for APIs
    assign_public_ip = true
  }

  # No load_balancer block — worker is not HTTP-facing, it polls SQS
}

# --- Frontend ECS Service ---

resource "aws_ecs_service" "frontend" {
  name            = "${var.app_name}-frontend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.frontend.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = [aws_subnet.public_a.id, aws_subnet.public_b.id]
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "${var.app_name}-frontend"
    container_port   = 80
  }

  depends_on = [aws_lb_listener.http]
}
