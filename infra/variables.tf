variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Short name used to prefix all resources"
  type        = string
  default     = "gmra-calculator"
}

variable "backend_image_tag" {
  description = "Docker image tag for the backend"
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  description = "Docker image tag for the frontend"
  type        = string
  default     = "latest"
}

variable "domain_name" {
  description = "Root domain purchased from Namecheap (e.g. getmerc.com)"
  type        = string
}

# --- Secrets (set in terraform.tfvars, never commit that file) ---

variable "census_api_key" {
  description = "US Census API key"
  type        = string
  sensitive   = true
}

variable "mapbox_api_key" {
  description = "Mapbox API key"
  type        = string
  sensitive   = true
}

variable "alphasophia_api_key" {
  description = "AlphaSophia API key"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend API key for transactional email (starts with re_…)"
  type        = string
  sensitive   = true
}

variable "resend_dkim_value" {
  description = "TXT value for resend._domainkey DKIM record (provided by Resend dashboard)"
  type        = string
}

variable "resend_mx_value" {
  description = "MX record value for the send subdomain (provided by Resend dashboard, e.g. feedback-smtp.us-east-1.amazonses.com)"
  type        = string
}

variable "resend_spf_value" {
  description = "TXT SPF value for the send subdomain (provided by Resend dashboard, e.g. v=spf1 include:amazonses.com ~all)"
  type        = string
}

variable "stripe_secret_key" {
  description = "Stripe secret key (starts with sk_test_ or sk_live_)"
  type        = string
  sensitive   = true
}

variable "stripe_webhook_secret" {
  description = "Stripe webhook signing secret (starts with whsec_)"
  type        = string
  sensitive   = true
}

variable "stripe_publishable_key" {
  description = "Stripe publishable key (starts with pk_test_ or pk_live_) — baked into the frontend Docker build"
  type        = string
}
