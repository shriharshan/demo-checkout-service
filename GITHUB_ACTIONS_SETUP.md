# GitHub Actions CI/CD Setup Guide

## Quick Start

### 1. Push to GitHub

```bash
cd demo-checkout-service

# Add GitHub remote
git remote add origin https://github.com/shriharshan/demo-checkout-service.git

# Push to GitHub
git push -u origin main
```

If you encounter "remote already exists", update it:
```bash
git remote set-url origin https://github.com/shriharshan/demo-checkout-service.git
git push -u origin main
```

---

## 2. Configure GitHub Secrets

Go to: **GitHub repo → Settings → Secrets and variables → Actions**

### Required Secrets

| Secret Name | Value | Where to Get |
|-------------|-------|--------------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key | AWS IAM Console |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key | AWS IAM Console |

### Required Variables (Optional)

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `FAULT_SCENARIO` | `deployment_config_bug` | Default fault scenario |

**How to add secrets:**
1. Click "New repository secret"
2. Name: `AWS_ACCESS_KEY_ID`
3. Value: `<your-aws-access-key>`
4. Click "Add secret"
5. Repeat for `AWS_SECRET_ACCESS_KEY`

---

## 3. GitHub Environments (Optional but Recommended)

Create a "development" environment:

1. Go to **Settings → Environments**
2. Click "New environment"
3. Name: `development`
4. (Optional) Add protection rules:
   - Required reviewers
   - Wait timer
   - Deployment branches (main only)

---

## Workflow Triggers

The pipeline runs on:
- ✅ **Push to main/master** - Auto-deploys to dev
- ✅ **Pull requests** - Runs tests only, no deploy
- ✅ **Manual trigger** - Via "Actions" tab → "Run workflow"

---

## Pipeline Stages

### Stage 1: Test (Always runs)
- Install dependencies with `uv`
- Run `pytest` with coverage
- Type checking with `mypy`
- Linting with `ruff`

### Stage 2: Package (After tests pass)
- Run `scripts/package.sh`
- Upload `lambda-package.zip` as artifact
- Artifact retained for 7 days

### Stage 3: Deploy (Only on main branch)
- Download Lambda package
- Configure AWS credentials
- Run Terraform init/plan/apply
- Output Lambda Function URL

---

## Viewing Results

### Deployment Summary
After deployment, check the **Actions** tab. Each run shows:
- ✅ Environment deployed
- 🚀 Function URL
- 📦 Package name
- 🕒 Deployment timestamp

### Logs
Click any workflow run → Click job name → Expand steps

---

## Local Testing Before Push

```bash
# Test the workflow locally with act (optional)
brew install act  # macOS
# or
sudo apt install act  # Linux

# Run workflow locally
act -j test
```

---

## Troubleshooting

### "Terraform init failed"
- Check AWS credentials are valid
- Verify IAM permissions for Lambda, CloudWatch, IAM

### "No package found"
- Ensure `scripts/package.sh` runs successfully locally
- Check Python dependencies are in `pyproject.toml`

### "AWS credentials not configured"
- Verify secrets `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` exist
- Check secret names match exactly

---

## Next Steps After Push

1. ✅ Push code to GitHub
2. ✅ Add AWS secrets
3. ✅ Trigger workflow (push to main or manual)
4. ✅ Check deployment summary
5. ✅ Test Lambda function URL

**Ready!** Every push to main will auto-deploy. 🚀
