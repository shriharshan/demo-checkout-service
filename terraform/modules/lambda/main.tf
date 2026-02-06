resource "aws_lambda_function" "demo_checkout" {
  function_name = var.function_name
  role          = aws_iam_role.lambda_exec.arn
  
  filename         = "${path.module}/../../../lambda-package.zip"
  source_code_hash = filebase64sha256("${path.module}/../../../lambda-package.zip")
  
  runtime       = "python3.12"
  handler       = "lambda_handler.handler"
  timeout       = var.timeout
  memory_size   = var.memory_size
  
  environment {
    variables = var.environment_vars
  }
  
  logging_config {
    log_format = "JSON"
    log_group  = aws_cloudwatch_log_group.lambda_logs.name
  }
  
  # Lambda Powertools layer
  layers = [
    "arn:aws:lambda:${data.aws_region.current.name}:017000801446:layer:AWSLambdaPowertoolsPythonV2:59"
  ]
}

resource "aws_iam_role" "lambda_exec" {
  name = "${var.function_name}-exec-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 1  # Cost saving for demo
}

# EventBridge traffic generator DISABLED to avoid IAM permission requirements
# Requires: events:PutRule, events:PutTargets permissions
# You can invoke the Lambda manually via Function URL instead

# resource "aws_cloudwatch_event_rule" "traffic_generator" {
#   name                = "${var.function_name}-traffic"
#   description         = "Generate demo traffic every 5 minutes"
#   schedule_expression = "rate(5 minutes)"
#   state               = "DISABLED"
# }

# resource "aws_cloudwatch_event_target" "invoke_lambda" {
#   rule      = aws_cloudwatch_event_rule.traffic_generator.name
#   target_id = "DemoCheckoutLambda"
#   arn       = aws_lambda_function.demo_checkout.arn
#   
#   input = jsonencode({
#     order_id = "AUTO-GENERATED"
#   })
# }

# resource "aws_lambda_permission" "allow_eventbridge" {
#   statement_id  = "AllowEventBridge"
#   action        = "lambda:InvokeFunction"
#   function_name = aws_lambda_function.demo_checkout.function_name
#   principal     = "events.amazonaws.com"
#   source_arn    = aws_cloudwatch_event_rule.traffic_generator.arn
# }


data "aws_region" "current" {}

output "function_name" {
  value = aws_lambda_function.demo_checkout.function_name
}

output "function_arn" {
  value = aws_lambda_function.demo_checkout.arn
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda_logs.name
}
