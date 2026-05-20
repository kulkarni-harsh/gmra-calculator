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

variable "google_api_key" {
  description = "Google API key"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend API key for transactional email (starts with re_…)"
  type        = string
  sensitive   = true
}

variable "resend_dkim_value" {
  description = "TXT value for resend._domainkey DKIM record (from Resend dashboard)"
  type        = string
}

variable "resend_mx_value" {
  description = "MX record value for the send subdomain (from Resend dashboard)"
  type        = string
}

variable "resend_spf_value" {
  description = "TXT SPF value for the send subdomain"
  type        = string
}

variable "ns_records" {
  description = "4 Route 53 nameserver values to pin in the NS record (must match what's configured in your registrar). Leave empty on first deploy — fill in after AWS assigns nameservers."
  type        = list(string)
  default     = []
}

variable "dmarc_value" {
  description = "TXT DMARC policy record value"
  type        = string
  default     = "v=DMARC1; p=none;"
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

variable "api_key_wix" {
  description = "Static key used by the Wix Velo backend to call MERC API. Generate with `openssl rand -base64 36`."
  type        = string
  sensitive   = true
}

variable "api_key_react" {
  description = "Static key used by our own React frontend (mostly via same-origin bypass, but needed for SSR/local dev)."
  type        = string
  sensitive   = true
}

variable "auth_enforced" {
  description = "When true, the API requires an X-API-Key header (or matching internal Origin). Set to false during initial rollout."
  type        = bool
  default     = false
}

variable "internal_origins" {
  description = "Comma-separated list of allowed Origin header values that bypass the API-key check (our own React deployments)."
  type        = string
  default     = ""
}

variable "openapi_public" {
  description = "When true, /docs and /openapi.json are publicly reachable. Set false in prod."
  type        = bool
  default     = true
}

variable "frontend_enabled" {
  description = "When false, the React frontend ECS service is stopped (desired_count=0) and the ALB default route forwards to the backend. Use when Wix handles the frontend."
  type        = bool
  default     = true
}

variable "worker_enabled" {
  description = "When false, the worker ECS service runs with desired_count=0 (no Fargate tasks, no cost). Set false during development or when no report jobs are expected."
  type        = bool
  default     = true
}

variable "backend_enabled" {
  description = "When false, the backend ECS service runs with desired_count=0. Note: api.yourdomain.com will return 503 while disabled — only use during development when Wix integration is not needed."
  type        = bool
  default     = true
}

# --- Wix custom-domain DNS ---
# Wix hosts the public-facing site at apex (and www). The Wix dashboard gives
# you A record IP(s) for the apex and a CNAME target for www. Fill these in
# once the Wix site is connected; while empty, apex/www remain pointed at the
# ALB (rollback / pre-cutover behaviour).

variable "wix_apex_a_records" {
  description = "Wix-provided A record IP addresses for the apex domain. When empty, apex stays pointed at the ALB."
  type        = list(string)
  default     = []
}

variable "wix_www_cname_target" {
  description = "Wix-provided CNAME target for the www subdomain (e.g. 'a-record.wixdns.net' or similar). When empty, www stays pointed at the ALB."
  type        = string
  default     = ""
}
