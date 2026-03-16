#!/bin/bash
# Runs once when LocalStack finishes booting.
# Creates the SQS queues and DynamoDB table that the app expects.
set -e

echo "==> Creating SQS queues..."

# Dead-letter queue first (main queue references its ARN)
awslocal sqs create-queue --queue-name merc-jobs-dlq

DLQ_ARN=$(awslocal sqs get-queue-attributes \
  --queue-url http://localhost:4566/000000000000/merc-jobs-dlq \
  --attribute-names QueueArn \
  --query 'Attributes.QueueArn' \
  --output text)

awslocal sqs create-queue \
  --queue-name merc-jobs \
  --attributes VisibilityTimeout=900,MessageRetentionPeriod=86400

echo "==> Creating DynamoDB table..."

awslocal dynamodb create-table \
  --table-name merc-jobs \
  --attribute-definitions AttributeName=job_id,AttributeType=S \
  --key-schema AttributeName=job_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

echo "==> Creating S3 bucket..."
awslocal s3 mb s3://merc-reports

echo "==> LocalStack init complete."
echo "    SQS queue URL : http://localhost:4566/000000000000/merc-jobs"
echo "    DynamoDB table: merc-jobs"
echo "    S3 bucket     : merc-reports"
