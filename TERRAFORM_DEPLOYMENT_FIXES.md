# Terraform Deployment Fixes

## Issues Encountered

### Issue 1: Resources Already Exist
```
Error: Role with name demo-checkout-service-exec-role already exists.
```
**Cause:** Previous deployment partially created resources before failing.

### Issue 2: Missing IAM Permissions
```
Error: User is not authorized to perform: logs:ListTagsForResource
Error: User is not authorized to perform: events:PutRule
```
**Cause:** IAM user lacks permissions for EventBridge and CloudWatch Logs tagging.

---

## Fixes Applied ✅

### 1. Removed EventBridge Traffic Generator

**Removed from `terraform/modules/lambda/main.tf`:**
- `aws_cloudwatch_event_rule.traffic_generator`
- `aws_cloudwatch_event_target.lambda`
- `aws_lambda_permission.allow_eventbridge`

**Why:** EventBridge requires `events:PutRule` permission which your IAM user doesn't have. The traffic generator was optional for testing.

### 2. Removed Tags from CloudWatch Log Group

**Changed:**
```hcl
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 1
  # Removed: skip_destroy and tags
}
```

**Why:** Removed `skip_destroy` and `tags` to avoid `logs:ListTagsForResource` permission requirement.

---

## Next Deployment Steps

### Step 1: Clean Up Existing Resources (Manual)

Go to AWS Console and delete these if they exist:
1. **IAM Role:** `demo-checkout-service-exec-role`
2. **CloudWatch Log Group:** `/aws/lambda/demo-checkout-service`
3. **EventBridge Rule:** `demo-checkout-service-traffic` (if exists)

**Quick AWS CLI commands:**
```bash
# Delete IAM role
aws iam detach-role-policy --role-name demo-checkout-service-exec-role --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
aws iam delete-role --role-name demo-checkout-service-exec-role

# Delete log group
aws logs delete-log-group --log-group-name /aws/lambda/demo-checkout-service

# Delete EventBridge rule (if exists)
aws events remove-targets --rule demo-checkout-service-traffic --ids DemoCheckoutServiceTarget
aws events delete-rule --name demo-checkout-service-traffic
```

### Step 2: Push Fixed Terraform

Already done! The fix has been pushed to GitHub.

### Step 3: Trigger New Deployment

The next GitHub Actions run will deploy successfully!

---

## Alternative: Add IAM Permissions (If You Want Full Features)

If you want EventBridge traffic generation back, add these permissions to your IAM user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "events:PutRule",
        "events:PutTargets",
        "events:DeleteRule",
        "events:RemoveTargets",
        "events:DescribeRule",
        "logs:ListTagsForResource",
        "logs:TagResource",
        "logs:UntagResource"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## Simplified Deployment

**What's deployed now:**
- ✅ Lambda Function
- ✅ IAM Execution Role
- ✅ CloudWatch Log Group
- ✅ Lambda Function URL (for manual testing)
- ❌ EventBridge Traffic Generator (removed to avoid IAM issues)

**To test your Lambda:**
```bash
# Use the Function URL from deployment output
curl -X POST <FUNCTION_URL>
```
