# ─── Mailgun DNS Records ──────────────────────────────────────────────────────
#
# Copy all values from Mailgun → Sending → Domains → your domain → DNS records
# into terraform.tfvars, then run terraform apply.
#
# Records managed here:
#   SPF    yourdomain.com TXT        authorise Mailgun to send from your domain
#   DKIM   mailo._domainkey.…  TXT   cryptographic signing key
#   MX ×2  yourdomain.com           let Mailgun receive replies/bounces
#   CNAME  email.yourdomain.com     click/open tracking
#   DMARC  _dmarc.yourdomain.com    policy for failed SPF/DKIM checks
# ─────────────────────────────────────────────────────────────────────────────

variable "mailgun_dkim_selector" {
  description = "Subdomain prefix before ._domainkey in Mailgun's DKIM record (e.g. 'mailo')"
  type        = string
  default     = "mailo"
}

variable "mailgun_dkim_key" {
  description = "Full DKIM TXT value from Mailgun (the entire 'k=rsa; p=...' string)"
  type        = string
}

variable "mailgun_api_key" {
  description = "Mailgun private API key (starts with key-…)"
  type        = string
  sensitive   = true
}

# SPF — single record; only one SPF record is allowed per domain
resource "aws_route53_record" "spf" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = 600
  records = ["v=spf1 include:mailgun.org ~all"]
}

# DKIM — Mailgun's RSA signing key; Route 53 handles the 255-char chunking automatically
resource "aws_route53_record" "mailgun_dkim" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "${var.mailgun_dkim_selector}._domainkey.${var.domain_name}"
  type    = "TXT"
  ttl     = 600
  records = [var.mailgun_dkim_key]
}

# MX — Mailgun receives replies and bounces on your behalf
resource "aws_route53_record" "mailgun_mx" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = 600
  records = [
    "10 mxa.mailgun.org",
    "10 mxb.mailgun.org",
  ]
}

# CNAME — Mailgun rewrites links through this subdomain for click/open tracking
resource "aws_route53_record" "mailgun_tracking" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "email.${var.domain_name}"
  type    = "CNAME"
  ttl     = 600
  records = ["mailgun.org"]
}

# DMARC — quarantine emails that fail SPF/DKIM; required by Gmail/Yahoo since 2024
resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "_dmarc.${var.domain_name}"
  type    = "TXT"
  ttl     = 600
  records = ["v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@${var.domain_name}"]
}
