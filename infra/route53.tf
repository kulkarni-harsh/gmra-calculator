resource "aws_route53_zone" "main" {
  name = var.domain_name
}

# Pins nameservers once ns_records is populated in tfvars.
# Leave ns_records empty on first deploy, then fill in the values AWS assigns
# and run apply again to lock them in (prevents silent reassignment on zone re-creation).
resource "aws_route53_record" "ns" {
  count = length(var.ns_records) > 0 ? 1 : 0

  zone_id         = aws_route53_zone.main.zone_id
  name            = var.domain_name
  type            = "NS"
  ttl             = 172800
  allow_overwrite = true

  records = var.ns_records
}

# --- Public-site DNS (apex + www) ---
# When wix_apex_a_records / wix_www_cname_target are set, apex + www point at
# Wix (which serves the public site). Otherwise they keep pointing at the ALB
# (legacy / pre-cutover / rollback). Only one of each pair exists at a time.

# Apex → Wix (when configured)
resource "aws_route53_record" "apex_wix" {
  count = length(var.wix_apex_a_records) > 0 ? 1 : 0

  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"
  ttl     = 3600
  records = var.wix_apex_a_records
}

# Apex → ALB (fallback when Wix not yet configured)
# Uses an ALIAS record (AWS-specific). Unlike CNAME, ALIAS works at the root domain.
resource "aws_route53_record" "apex_alb" {
  count = length(var.wix_apex_a_records) > 0 ? 0 : 1

  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Preserve existing state when migrating from the old single-resource layout.
moved {
  from = aws_route53_record.apex
  to   = aws_route53_record.apex_alb[0]
}

# www → Wix (when configured)
resource "aws_route53_record" "www_wix" {
  count = length(var.wix_www_cname_target) > 0 ? 1 : 0

  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 3600
  records = [var.wix_www_cname_target]
}

# www → ALB (fallback when Wix not yet configured)
resource "aws_route53_record" "www_alb" {
  count = length(var.wix_www_cname_target) > 0 ? 0 : 1

  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

moved {
  from = aws_route53_record.www
  to   = aws_route53_record.www_alb[0]
}

# api: api.yourdomain.com → ALB
# This is the hostname the Wix Velo backend calls. Always pointed at the ALB.
resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# Resend DKIM — verifies outbound email signing key
resource "aws_route53_record" "resend_dkim" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "resend._domainkey.${var.domain_name}"
  type    = "TXT"
  ttl     = 300

  records = [var.resend_dkim_value]
}

# Resend bounce/feedback routing via SES
resource "aws_route53_record" "resend_mx" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "send.${var.domain_name}"
  type    = "MX"
  ttl     = 300

  records = [var.resend_mx_value]
}

# SPF for the send subdomain — authorises SES to send on its behalf
resource "aws_route53_record" "resend_spf" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "send.${var.domain_name}"
  type    = "TXT"
  ttl     = 300

  records = [var.resend_spf_value]
}

# DMARC policy — p=none means monitor-only (no enforcement yet)
resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "_dmarc.${var.domain_name}"
  type    = "TXT"
  ttl     = 300

  records = [var.dmarc_value]
}
