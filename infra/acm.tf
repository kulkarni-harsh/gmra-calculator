# ACM (AWS Certificate Manager) — free SSL cert for the ALB.
# Primary name is api.<domain> (always served by ALB). apex and www are added
# as SANs only when the public site is actually being served on this domain
# (either Wix vars are set, or frontend_enabled=true). When neither, the cert
# has a single name and the apex/www aren't in DNS — see route53.tf.

resource "aws_acm_certificate" "main" {
  domain_name = "api.${var.domain_name}"
  subject_alternative_names = concat(
    (length(var.wix_apex_a_records) > 0 || var.frontend_enabled) ? [var.domain_name] : [],
    (length(var.wix_www_cname_target) > 0 || var.frontend_enabled) ? ["www.${var.domain_name}"] : [],
  )
  validation_method = "DNS"

  # Must destroy old cert before creating new one when domain changes
  lifecycle {
    create_before_destroy = true
  }
}

# Terraform reads the CNAME records that ACM requires for proof-of-ownership
# and creates them in Route 53 automatically.
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.main.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  zone_id         = aws_route53_zone.main.zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

# Terraform waits here until ACM confirms the cert is issued.
# This only works after Namecheap nameservers are pointed at Route 53
# and DNS has propagated (~5-30 min).
resource "aws_acm_certificate_validation" "main" {
  certificate_arn         = aws_acm_certificate.main.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}
