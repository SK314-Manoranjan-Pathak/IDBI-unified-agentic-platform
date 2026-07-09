#!/bin/bash
# upload-data.sh — Upload model artifacts to S3, then trigger EC2 sync.
# Run this from your local machine after CloudFormation stack is deployed.
#
# Usage:
#   bash deploy/upload-data.sh                              # uses default profile
#   bash deploy/upload-data.sh --profile idbi-deploy        # uses SSO profile
#   bash deploy/upload-data.sh --stack my-stack --profile idbi-deploy
#
# Prerequisites:
#   - AWS CLI v2 configured (aws configure sso OR aws configure)
#   - If using SSO: run `aws sso login --profile YOUR_PROFILE` first
#   - Stack deployed
#   - data/processed/ and data/models/ exist locally with pipeline outputs

set -e

# --- Parse arguments ---
STACK_NAME="idbi-agentic-platform"
REGION="ap-south-1"
PROFILE_ARG=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --profile)
      PROFILE_ARG="--profile $2"
      shift 2
      ;;
    --stack)
      STACK_NAME="$2"
      shift 2
      ;;
    --region)
      REGION="$2"
      shift 2
      ;;
    *)
      # Positional: stack name (backwards compat)
      STACK_NAME="$1"
      shift
      ;;
  esac
done

echo "=== IDBI Platform — Upload Model Artifacts ==="
echo "  Stack:   $STACK_NAME"
echo "  Region:  $REGION"
echo "  Profile: ${PROFILE_ARG:-default}"
echo ""

# --- Get bucket name from stack outputs ---
BUCKET=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='DataBucketName'].OutputValue" \
  --output text --region "$REGION" $PROFILE_ARG)

if [ -z "$BUCKET" ] || [ "$BUCKET" = "None" ]; then
  echo "ERROR: Could not find DataBucketName in stack outputs."
  echo "Make sure the stack '$STACK_NAME' is fully deployed."
  echo "Run: aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION $PROFILE_ARG"
  exit 1
fi

echo "S3 Bucket: $BUCKET"
echo ""

# --- Upload processed data ---
echo "[1/3] Uploading data/processed/ ..."
aws s3 sync data/processed/ "s3://$BUCKET/data/processed/" \
  --region "$REGION" $PROFILE_ARG \
  --exclude "*.gitkeep"

# --- Upload model artifacts ---
echo "[2/3] Uploading data/models/ ..."
aws s3 sync data/models/ "s3://$BUCKET/data/models/" \
  --region "$REGION" $PROFILE_ARG \
  --exclude "*.gitkeep"

echo ""
echo "Upload complete!"
echo ""

# --- Trigger EC2 to pull from S3 and restart ---
INSTANCE_ID=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" \
  --output text --region "$REGION" $PROFILE_ARG)

echo "[3/3] Triggering EC2 ($INSTANCE_ID) to sync from S3 and restart ..."
COMMAND_ID=$(aws ssm send-command \
  --instance-ids "$INSTANCE_ID" \
  --document-name "AWS-RunShellScript" \
  --parameters "commands=[
    'aws s3 sync s3://$BUCKET/data/ /opt/idbi-platform/data/ --region $REGION',
    'systemctl restart idbi-backend',
    'echo DONE'
  ]" \
  --region "$REGION" $PROFILE_ARG \
  --output text \
  --query "Command.CommandId")

echo "  SSM Command ID: $COMMAND_ID"
echo ""
echo "=== All done! ==="
echo ""
echo "Wait ~30 seconds for the backend to restart with new models, then verify:"
echo "  aws ssm start-session --target $INSTANCE_ID --region $REGION $PROFILE_ARG"
echo "  curl http://localhost:8000/health"
echo ""
echo "Or get your public URL:"
echo "  aws cloudformation describe-stacks --stack-name $STACK_NAME \\"
echo "    --query \"Stacks[0].Outputs[?OutputKey=='CloudFrontURL'].OutputValue\" \\"
echo "    --output text --region $REGION $PROFILE_ARG"
