#!/usr/bin/env bash
set -euo pipefail

# ── Workspace ─────────────────────────────────────────────────────────────────
WORKSPACE="${2:-$(cd "$(dirname "${BASH_SOURCE[0]}")/infra" && terraform workspace show)}"

case "$WORKSPACE" in
  client)
    ACCOUNT_ID="800728769883"
    PUBLISHABLE_STRIPE_KEY="pk_test_51TBuNhHhWMiyKgBo9ft6mCt4Hs1sSWMUtuVVCCXthHaDYWdjk7DB7IVZcSfyR1ynpk4HqRLtIspKQckfvNY0O7CC00IQPnMXDp"
    ;;
  personal)
    ACCOUNT_ID="707057771327"
    PUBLISHABLE_STRIPE_KEY="pk_test_51TBuNhHhWMiyKgBo9ft6mCt4Hs1sSWMUtuVVCCXthHaDYWdjk7DB7IVZcSfyR1ynpk4HqRLtIspKQckfvNY0O7CC00IQPnMXDp"
    ;;
  *)
    echo "Unknown workspace '${WORKSPACE}'. Usage: ./deploy.sh [tag] [client|personal]"
    exit 1
    ;;
esac

# ── Config ────────────────────────────────────────────────────────────────────
AWS_REGION="us-east-1"
AWS_PROFILE="$WORKSPACE"
CLUSTER="gmra-calculator-cluster"
ECR_BASE="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
BACKEND_REPO="${ECR_BASE}/gmra-calculator-backend"
FRONTEND_REPO="${ECR_BASE}/gmra-calculator-frontend"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Derive frontend_enabled from the workspace's tfvars so the script stays in
# sync with the infra config. Default true if the var is absent (matches the
# variable default in variables.tf).
TFVARS_FILE="${SCRIPT_DIR}/infra/${WORKSPACE}.tfvars"
if [[ -f "$TFVARS_FILE" ]] && grep -qE '^frontend_enabled\s*=\s*false' "$TFVARS_FILE"; then
  FRONTEND_ENABLED="false"
else
  FRONTEND_ENABLED="true"
fi

# ── Args ──────────────────────────────────────────────────────────────────────
TAG="${1:-latest}"

log() { echo "[$(date '+%H:%M:%S')] [$WORKSPACE] $*"; }

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Workspace : $WORKSPACE"
echo "  Account   : $ACCOUNT_ID"
echo "  Tag       : $TAG"
echo "  Frontend  : $FRONTEND_ENABLED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── ECR login ─────────────────────────────────────────────────────────────────
log "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" --profile "$AWS_PROFILE" \
  | docker login --username AWS --password-stdin "$ECR_BASE"

# ── Build & push backend ──────────────────────────────────────────────────────
log "Building & pushing backend image (tag: $TAG)..."
docker buildx build \
  --platform linux/amd64 \
  --push \
  -t "${BACKEND_REPO}:${TAG}" \
  "${SCRIPT_DIR}/backend"

if [[ "$FRONTEND_ENABLED" == "true" ]]; then
  log "Building & pushing frontend image (tag: $TAG)..."
  docker buildx build \
    --platform linux/amd64 \
    --push \
    --build-arg "VITE_STRIPE_PUBLISHABLE_KEY=${PUBLISHABLE_STRIPE_KEY}" \
    -t "${FRONTEND_REPO}:${TAG}" \
    "${SCRIPT_DIR}/frontend"
else
  log "Skipping frontend image (frontend_enabled=false)."
fi

# ── Determine which services to redeploy ──────────────────────────────────────
SERVICES=(backend worker)
if [[ "$FRONTEND_ENABLED" == "true" ]]; then
  SERVICES=(frontend backend worker)
fi

# ── Force new ECS deployments ─────────────────────────────────────────────────
for SERVICE in "${SERVICES[@]}"; do
  log "Deploying ECS service: $SERVICE..."
  aws ecs update-service \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --cluster "$CLUSTER" \
    --service "gmra-calculator-${SERVICE}" \
    --force-new-deployment \
    --query "service.{name:serviceName,status:status,desired:desiredCount}" \
    --output table
done

# ── Wait for stability ────────────────────────────────────────────────────────
log "Waiting for services to stabilize..."
for SERVICE in "${SERVICES[@]}"; do
  log "  Waiting on gmra-calculator-${SERVICE}..."
  aws ecs wait services-stable \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --cluster "$CLUSTER" \
    --services "gmra-calculator-${SERVICE}"
  log "  gmra-calculator-${SERVICE} is stable."
done

log "Deploy complete."
