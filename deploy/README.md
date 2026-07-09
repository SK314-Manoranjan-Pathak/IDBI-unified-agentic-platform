# Deployment Guide — IDBI Unified Agentic Platform

## Architecture

```
Users → CloudFront (HTTPS) → ALB (HTTP, port 80) → EC2 Nginx (port 80)
                                                         │
                                                         ├─ /api/*  → FastAPI (port 8000)
                                                         └─ /*      → Next.js (port 3000)
```

- EC2 is in a **private subnet** (no public IP)
- ALB is in **public subnets** (internet-facing, but restricted to CloudFront)
- NAT Gateway provides outbound internet for EC2 (updates, packages)
- All managed via **CloudFormation** (single stack)

## Prerequisites

1. **AWS Account** with appropriate access (Admin or PowerUser permission set)
2. **AWS CLI v2** installed and configured with SSO:
   ```bash
   # One-time SSO setup
   aws configure sso
   # Enter: SSO start URL, region, and choose a profile name (e.g. idbi-deploy)

   # Login before each session (opens browser)
   aws sso login --profile idbi-deploy

   # Set as default for your terminal (so you don't need --profile every time)
   # Linux/Mac/Git Bash:
   export AWS_PROFILE=idbi-deploy
   # Windows CMD:
   set AWS_PROFILE=idbi-deploy
   # Windows PowerShell:
   $env:AWS_PROFILE = "idbi-deploy"
   ```
3. **EC2 Key Pair** in `ap-south-1`:
   - AWS Console → EC2 → Key Pairs → Create key pair
   - Save the `.pem` file (you likely won't need it — SSM is used for access)
4. **Repository pushed to GitHub** with all latest code (including `deploy/` folder)
5. **ML Pipeline already run locally** (so `data/processed/` and `data/models/` exist)

## Step 1: Deploy the Stack

```bash
aws cloudformation deploy \
  --template-file deploy/cloudformation.yaml \
  --stack-name idbi-agentic-platform \
  --region ap-south-1 \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    KeyPairName=YOUR_KEY_PAIR_NAME \
    GitRepoUrl=https://github.com/SK314-Manoranjan-Pathak/IDBI-unified-agentic-platform.git \
    GitBranch=main \
    InstanceType=t3.xlarge
```

**Wait ~12-15 minutes** for AWS to provision all resources. Monitor progress:
```bash
aws cloudformation describe-stack-events \
  --stack-name idbi-agentic-platform \
  --region ap-south-1 \
  --query "StackEvents[0:5].[Timestamp,ResourceStatus,ResourceType]" \
  --output table
```


## Step 2: Upload Model Artifacts

The ML models and feature matrix are not in git (they're gitignored). Upload them via S3:

```bash
# From your local project root (where data/ folder exists):
bash deploy/upload-data.sh --profile idbi-deploy
```

Or if you already set `AWS_PROFILE` in your terminal:
```bash
bash deploy/upload-data.sh
```

This script:
1. Finds the S3 bucket created by CloudFormation
2. Uploads `data/processed/` and `data/models/` to S3 (~25 MB)
3. Triggers the EC2 instance to pull from S3 via SSM
4. Restarts the backend service to load new models

**Windows users:** Run this in Git Bash or WSL, not cmd.

## Step 3: Verify the Deployment

```bash
# Get the CloudFront URL
aws cloudformation describe-stacks \
  --stack-name idbi-agentic-platform \
  --query "Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue" \
  --output text --region ap-south-1
```

Open that URL in your browser. You should see the FinPulse dashboard.

**If you need to troubleshoot on EC2:**
```bash
# Get instance ID
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name idbi-agentic-platform \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" \
  --output text --region ap-south-1)

# Start SSM session (no SSH key needed)
aws ssm start-session --target $INSTANCE_ID --region ap-south-1

# Once on EC2:
systemctl status idbi-backend     # Check backend
pm2 status                        # Check frontend
curl http://localhost:8000/health  # API health
curl http://localhost:3000         # Frontend
cat /var/log/user-data.log        # Bootstrap log
journalctl -u idbi-backend -n 50  # Backend logs
```

## Step 4: Future Updates

After pushing code changes to GitHub:

```bash
# Connect to EC2 via SSM
aws ssm start-session --target $INSTANCE_ID --region ap-south-1

# On EC2:
bash /opt/idbi-platform/deploy/deploy.sh
```

Or trigger remotely via SSM:
```bash
aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["bash /opt/idbi-platform/deploy/deploy.sh"]' \
  --region ap-south-1
```

## Tear Down

To delete all resources and stop charges:
```bash
# Empty the S3 bucket first (CloudFormation can't delete non-empty buckets)
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name idbi-agentic-platform \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" \
  --output text --region ap-south-1)
aws s3 rm "s3://$BUCKET" --recursive --region ap-south-1

# Delete the stack
aws cloudformation delete-stack \
  --stack-name idbi-agentic-platform \
  --region ap-south-1
```

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| CloudFront returns 502 | EC2 still bootstrapping | Wait 5 min, check `/var/log/user-data.log` |
| ALB health check failing | Backend not started (no data) | Run `upload-data.sh`, then `systemctl restart idbi-backend` |
| Frontend loads but API calls fail | Nginx not routing `/api/*` | Check `nginx -t` and `systemctl status nginx` |
| SSM session won't connect | IAM role not attached | Verify instance profile in EC2 console |
| Stack creation fails | AMI ID wrong for region | Update AMI ID in CloudFormation `Mappings` section |

## Cost (Monthly, ap-south-1)

| Resource | Cost |
|----------|------|
| EC2 t3.xlarge (on-demand) | ~$120 |
| EBS 30 GB gp3 | ~$2.40 |
| ALB | ~$22 |
| NAT Gateway | ~$35 |
| CloudFront | ~$5-10 |
| S3 (minimal) | ~$0.10 |
| **Total** | **~$185-190/month** |

**Tip:** Use a Savings Plan for EC2 to save 30-40% ($72-84/month instead of $120).
