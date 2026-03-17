# ─── Email DNS ────────────────────────────────────────────────────────────────
#
# Sending is handled by Resend using the tryingmybest.site domain, which is
# configured directly in the Resend dashboard (no Route 53 records needed here).
#
# DMARC is kept for the app domain as a best-practice policy record.
# ─────────────────────────────────────────────────────────────────────────────

# Resend DKIM — proves Resend is authorized to sign mail for this domain
resource "aws_route53_record" "resend_dkim" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "resend._domainkey.${var.domain_name}"
  type    = "TXT"
  ttl     = 300
  records = [var.resend_dkim_value]
}

# Resend MX — routes bounces/feedback for the send subdomain through Resend
resource "aws_route53_record" "resend_mx" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "send.${var.domain_name}"
  type    = "MX"
  ttl     = 300
  records = [var.resend_mx_value]
}

# Resend SPF — authorizes Resend's infrastructure to send from the send subdomain
resource "aws_route53_record" "resend_spf" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "send.${var.domain_name}"
  type    = "TXT"
  ttl     = 300
  records = [var.resend_spf_value]
}

# DMARC — quarantine emails that fail SPF/DKIM; required by Gmail/Yahoo since 2024
resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "_dmarc.${var.domain_name}"
  type    = "TXT"
  ttl     = 600
  records = ["v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@${var.domain_name}"]
}
