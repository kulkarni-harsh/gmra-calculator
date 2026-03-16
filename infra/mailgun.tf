# ─── Email DNS ────────────────────────────────────────────────────────────────
#
# Sending is handled by Resend using the tryingmybest.site domain, which is
# configured directly in the Resend dashboard (no Route 53 records needed here).
#
# DMARC is kept for the app domain as a best-practice policy record.
# ─────────────────────────────────────────────────────────────────────────────

# DMARC — quarantine emails that fail SPF/DKIM; required by Gmail/Yahoo since 2024
resource "aws_route53_record" "dmarc" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "_dmarc.${var.domain_name}"
  type    = "TXT"
  ttl     = 600
  records = ["v=DMARC1; p=quarantine; rua=mailto:dmarc-reports@${var.domain_name}"]
}
