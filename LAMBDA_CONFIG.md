# Lambda Deployment Configuration

## Where Lambda Settings Are Defined

### Terraform Variables

**File:** `terraform/variables.tf`

This file defines all the configurable parameters for your Lambda deployment:

```hcl
variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "demo-checkout-service"  # ← Your Lambda function name
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory" {
  description = "Lambda memory in MB"
  type        = number
  default     = 512
}

variable "environment_vars" {
  description = "Environment variables for Lambda"
  type        = map(string)
  default     = {
    FAULT_SCENARIO = "normal"
  }
}
```

### How GitHub Actions Uses These

**In the workflow** (`.github/workflows/deploy.yml`):

```yaml
- name: Terraform Plan
  run: |
    cd terraform
    terraform plan -out=tfplan \
      -var="environment=dev" \
      -var="fault_scenario=${{ vars.FAULT_SCENARIO || 'normal' }}"
```

### Customizing Deployment

**Option 1: Change defaults in `terraform/variables.tf`**

```hcl
variable "function_name" {
  default = "my-custom-function-name"  # Change here
}

variable "lambda_memory" {
  default = 1024  # Increase memory
}
```

**Option 2: Pass variables in workflow**

Edit `.github/workflows/deploy.yml`:

```yaml
- name: Terraform Plan
  run: |
    cd terraform
    terraform plan -out=tfplan \
      -var="function_name=my-custom-name" \
      -var="lambda_memory=1024" \
      -var="environment=dev"
```

**Option 3: Use GitHub Variables**

Set in GitHub: **Settings → Secrets and variables → Variables**

- `FUNCTION_NAME` = `demo-checkout-service`
- `LAMBDA_MEMORY` = `1024`

Then use in workflow:
```yaml
-var="function_name=${{ vars.FUNCTION_NAME }}"
-var="lambda_memory=${{ vars.LAMBDA_MEMORY }}"
```

---

## AWS Access Configuration

**Q: Where are AWS credentials configured?**

**A: GitHub Secrets** (you already set these up!)

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ${{ env.AWS_REGION }}
```

The action uses your secrets to:
1. Authenticate with AWS
2. Run Terraform commands
3. Deploy Lambda to your AWS account

---

## What Gets Created in AWS

When the workflow runs Terraform, it creates:

1. **Lambda Function**
   - Name: `demo-checkout-service` (or your custom name)
   - Runtime: Python 3.12
   - Memory: 512 MB (default)
   - Timeout: 60 seconds

2. **IAM Role** 
   - Name: `demo-checkout-service-exec-role`
   - Permissions: Lambda execution + CloudWatch Logs

3. **CloudWatch Log Group**
   - Name: `/aws/lambda/demo-checkout-service`
   - Retention: 1 day

4. **Function URL** (Optional)
   - Public HTTP endpoint to invoke Lambda

---

## Quick Reference

| Setting | File | Default Value |
|---------|------|---------------|
| Function Name | `terraform/variables.tf` | `demo-checkout-service` |
| Memory | `terraform/variables.tf` | 512 MB |
| Timeout | `terraform/variables.tf` | 60 seconds |
| Region | `.github/workflows/deploy.yml` | `us-east-1` |
| AWS Credentials | GitHub Secrets | Your IAM keys |

**To change function name:** Edit `terraform/variables.tf` → `function_name` default value
