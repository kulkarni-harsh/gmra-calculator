# Dead-letter queue — receives messages that failed processing 3 times.
# Inspect this in the AWS console to debug stuck jobs.
resource "aws_sqs_queue" "jobs_dlq" {
  name                      = "${var.app_name}-jobs-dlq"
  message_retention_seconds = 1209600  # 14 days — plenty of time to investigate
}

# Main jobs queue
resource "aws_sqs_queue" "jobs" {
  name = "${var.app_name}-jobs"

  # Must be >= the worker's VisibilityTimeout (900s).
  # While a worker holds the message invisible, no other worker can steal it.
  visibility_timeout_seconds = 900

  # Keep unprocessed messages for 1 day (reports requested but worker was down)
  message_retention_seconds = 86400

  # After 3 failed receive-and-not-delete cycles, move to DLQ
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.jobs_dlq.arn
    maxReceiveCount     = 3
  })

  tags = { Name = "${var.app_name}-jobs" }
}

output "sqs_queue_url" {
  value       = aws_sqs_queue.jobs.url
  description = "SQS queue URL — set as SQS_QUEUE_URL env var in ECS tasks"
}
