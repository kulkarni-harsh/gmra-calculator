# Route 53 hosted zone — AWS becomes the authoritative DNS for your domain.
# These nameservers are already configured in Namecheap as Custom DNS.
# The explicit NS record below locks them in so a zone re-creation doesn't
# silently assign different nameservers (which would break DNS until Namecheap
# is updated again).

resource "aws_route53_zone" "main" {
  name = var.domain_name
}

# Explicit NS record — pins the nameservers to the ones already in Namecheap.
# allow_overwrite = true so Terraform can update the auto-created NS record AWS adds on zone creation.
resource "aws_route53_record" "ns" {
  zone_id         = aws_route53_zone.main.zone_id
  name            = var.domain_name
  type            = "NS"
  ttl             = 172800 # 48 hours — standard for NS records
  allow_overwrite = true

  records = [
    "ns-1241.awsdns-27.org.",
    "ns-1650.awsdns-14.co.uk.",
    "ns-214.awsdns-26.com.",
    "ns-750.awsdns-29.net.",
  ]
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
