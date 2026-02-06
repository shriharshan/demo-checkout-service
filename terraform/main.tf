terraform {
  required_version = ">= 1.6"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "lambda" {
  source = "./modules/lambda"
  
  function_name    = var.function_name
  environment_vars = var.environment_vars
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory
}

output "function_name" {
  value = module.lambda.function_name
}

output "function_arn" {
  value = module.lambda.function_arn
}

output "log_group_name" {
  value = module.lambda.log_group_name
}
