data "archive_file" "meadow_zip" {
  type        = "zip"
  source_dir  = "${path.module}/handlers/"
  output_path = "${path.module}/.meadow.zip"
}

variable "endpoints" {
  default = {
    "signup"      = "POST"
    "validate"    = "GET"
    "unsubscribe" = "GET"
  }
}

resource "aws_lambda_function" "members" {
  for_each         = var.endpoints
  filename         = data.archive_file.meadow_zip.output_path
  function_name    = each.key
  role             = aws_iam_role.members.arn
  handler          = "handler.${each.key}"
  source_code_hash = data.archive_file.meadow_zip.output_base64sha256
  runtime          = "python3.8"
  timeout          = 60
  publish          = true
}

resource "aws_lambda_permission" "members" {
  for_each      = var.endpoints
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.members[each.key].function_name
  principal     = "apigateway.amazonaws.com"
}

resource "aws_apigatewayv2_integration" "members" {
  for_each           = var.endpoints
  api_id             = aws_apigatewayv2_api.members.id
  integration_type   = "AWS_PROXY"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.members[each.key].invoke_arn
}

resource "aws_apigatewayv2_route" "members" {
  for_each  = var.endpoints
  api_id    = aws_apigatewayv2_api.members.id
  route_key = "${each.value} /${each.key}"
  target    = "integrations/${aws_apigatewayv2_integration.members[each.key].id}"
}

// Role and policy for handlers
resource "aws_iam_role" "members" {
  name = "meadow-lambda"
  inline_policy {
    name   = "meadow-lambda"
    policy = data.aws_iam_policy_document.meadow-lambda.json
  }
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      }
    }
  ]
}
EOF
}

data "aws_iam_policy_document" "meadow-lambda" {
  statement {
    effect = "Allow"

    resources = [
      "arn:aws:logs:*:*:*"
    ]

    actions = [
      "logs:CreateLogStream",
      "logs:CreateLogGroup",
      "logs:PutLogEvents"
    ]
  }

  statement {
    effect = "Allow"

    resources = [
      "*"
    ]

    actions = [
      "dynamodb:*"
    ]
  }
  statement {
    effect = "Allow"

    resources = [
      "*"
    ]

    actions = [
      "ses:*"
    ]
  }
  statement {
    effect = "Allow"

    resources = [
      "*"
    ]

    actions = [
      "ssm:*"
    ]
  }

  statement {
    effect = "Allow"

    resources = [
      "${aws_s3_bucket.barn.arn}/*"
    ]

    actions = [
      "s3:GetObject"
    ]
  }
}

// Send newsletter lambda
resource "aws_lambda_function" "send_newsletter" {
  filename         = data.archive_file.meadow_zip.output_path
  function_name    = "send_newsletter"
  role             = aws_iam_role.members.arn
  handler          = "handler.send_newsletter"
  source_code_hash = data.archive_file.meadow_zip.output_base64sha256
  runtime          = "python3.8"
  timeout          = 60
  publish          = true
}