resource "aws_dynamodb_table" "jobs" {
  name         = "merc-jobs"
  billing_mode = "PAY_PER_REQUEST"  # no capacity planning needed; pay per read/write
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  # TTL: DynamoDB auto-deletes items whose 'ttl' unix timestamp has passed
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = { Name = "${var.app_name}-jobs" }
}
