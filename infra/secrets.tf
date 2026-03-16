# Single JSON secret containing all API keys.
# ECS injects individual keys via the "secretArn:jsonKey::" valueFrom syntax.
# recovery_window_in_days = 0 means immediate delete (good for dev/staging).

resource "aws_secretsmanager_secret" "api_keys" {
  name                    = "/${var.app_name}/api-keys"
  recovery_window_in_days = 0

  tags = { Name = "${var.app_name}-api-keys" }
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    OPENCAGE_API_KEY    = var.opencage_api_key
    CENSUS_API_KEY      = var.census_api_key
    MAPBOX_API_KEY      = var.mapbox_api_key
    ALPHASOPHIA_API_KEY = var.alphasophia_api_key
    MAILGUN_API_KEY     = var.mailgun_api_key
  })
}
