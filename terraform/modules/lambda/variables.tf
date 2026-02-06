variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
}

variable "memory_size" {
  description = "Lambda memory in MB"
  type        = number
}

variable "environment_vars" {
  description = "Environment variables for Lambda"
  type        = map(string)
}
