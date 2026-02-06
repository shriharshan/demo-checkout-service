# AWS Resource Cleanup Commands

## Problem
Your Terraform deployment is failing because these resources already exist from previous failed deployments:
- IAM Role: `demo-checkout-service-exec-role`
- CloudWatch Log Group: `/aws/lambda/demo-checkout-service`

## Solution: Delete Existing Resources

Run these AWS CLI commands to clean up:

### Method 1: AWS CLI (Recommended - Fastest)

```bash
# Configure AWS CLI with your credentials if not already done
aws configure
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region: us-east-1
# Default output format: json

# Step 1: Detach the policy from the IAM role
aws iam detach-role-policy \
  --role-name demo-checkout-service-exec-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole \
  --region us-east-1

# Step 2: Delete the IAM role
aws iam delete-role \
  --role-name demo-checkout-service-exec-role

# Step 3: Delete the CloudWatch Log Group
aws logs delete-log-group \
  --log-group-name /aws/lambda/demo-checkout-service \
  --region us-east-1

echo "✅ Cleanup complete! You can now run Terraform deploy again."
```

### Method 2: AWS Console (If CLI doesn't work)

**Delete IAM Role:**
1. Go to https://console.aws.amazon.com/iam/
2. Click "Roles" in left sidebar
3. Search for: `demo-checkout-service-exec-role`
4. Select it and click "Delete"
5. Confirm deletion

**Delete CloudWatch Log Group:**
1. Go to https://console.aws.amazon.com/cloudwatch/
2. Click "Log groups" in left sidebar
3. Search for: `/aws/lambda/demo-checkout-service`
4. Select it and click "Actions" → "Delete log group(s)"
5. Confirm deletion

---

## After Cleanup

Once you've deleted these resources, the GitHub Actions workflow will succeed on the next run!

**Trigger new deployment:**
```bash
cd demo-checkout-service
git commit --allow-empty -m "trigger: Deploy after cleanup"
git push origin main
```

**Monitor at:** https://github.com/shriharshan/demo-checkout-service/actions

---

## No Additional IAM Policies Needed

You don't need to add any IAM policies! Your current permissions are sufficient for:
- Creating Lambda functions
- Creating IAM roles
- Creating CloudWatch Log Groups

The only issue was that these resources already existed from previous attempts.
