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

# Apex: yourdomain.com → ALB
# Uses an ALIAS record (AWS-specific). Unlike CNAME, ALIAS works at the root domain.
resource "aws_route53_record" "apex" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = aws_lb.main.dns_name
    zone_id                = aws_lb.main.zone_id
    evaluate_target_health = true
  }
}

# www: www.yourdomain.com → ALB
resource "aws_route53_record" "www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
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
