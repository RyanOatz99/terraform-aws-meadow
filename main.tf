resource "aws_dynamodb_table" "members" {
  name           = var.dynamodb_table_name
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "partitionKey"
  range_key      = "sortKey"

  attribute {
    name = "partitionKey"
    type = "S"
  }

  attribute {
    name = "sortKey"
    type = "S"
  }
}

// Configure domain certificate
resource "aws_acm_certificate" "members" {
  domain_name       = var.domain_name
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "members_validation" {
  name    = tolist(aws_acm_certificate.members.domain_validation_options).0.resource_record_name
  type    = tolist(aws_acm_certificate.members.domain_validation_options).0.resource_record_type
  zone_id = var.zone_id
  records = [tolist(aws_acm_certificate.members.domain_validation_options).0.resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "members" {
  certificate_arn         = aws_acm_certificate.members.arn
  validation_record_fqdns = [aws_route53_record.members_validation.fqdn]

}

// Configure Domain
resource "aws_apigatewayv2_domain_name" "members" {
  domain_name = var.domain_name

  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.members.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_route53_record" "members" {
  name    = var.domain_name
  type    = "A"
  zone_id = var.zone_id

  alias {
    name                   = aws_apigatewayv2_domain_name.members.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.members.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}

// Configure API Gateway
resource "aws_apigatewayv2_api" "members" {
  name          = "membership-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "members" {
  api_id      = aws_apigatewayv2_api.members.id
  name        = "production"
  auto_deploy = true
}

resource "aws_apigatewayv2_api_mapping" "members" {
  api_id      = aws_apigatewayv2_api.members.id
  domain_name = aws_apigatewayv2_domain_name.members.id
  stage       = aws_apigatewayv2_stage.members.id
}

// AWS SSM Parameter
resource "aws_ssm_parameter" "members" {
  name  = "MeadowDictionary"
  type  = "String"
  value = <<EOF
{
  "organisation": "${var.organisation_name}",
  "table": "${var.dynamodb_table_name}",
  "domain": "${var.domain_name}",
  "region": "${var.region}"
}
EOF
}
