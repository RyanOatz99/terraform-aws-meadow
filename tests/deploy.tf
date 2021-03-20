terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
  backend "local" {}
}

provider "aws" {
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

module "meadow" {
  source              = "../"
  organisation_name   = "Meadow Testing"
  dynamodb_table_name = "meadow-users"
  zone_id             = "Z0113789CFPZ63JFOFKB"
  domain_name         = "meadow-testing.grassfed.tools"
  region              = "us-east-1"
  account_id          = data.aws_caller_identity.current.account_id
}
