#!/usr/bin/env bash
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
AWS_REGION="us-east-1"
ACCOUNT_ID="707057771327"
CLUSTER="gmra-calculator-cluster"
ECR_BASE="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

BACKEND_REPO="${ECR_BASE}/gmra-calculator-backend"
FRONTEND_REPO="${ECR_BASE}/gmra-calculator-frontend"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Args ──────────────────────────────────────────────────────────────────────
TAG="${1:-latest}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ── ECR login ─────────────────────────────────────────────────────────────────
log "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_BASE"

# ── Build & push backend ──────────────────────────────────────────────────────
log "Building & pushing backend image (tag: $TAG)..."
docker buildx build \
  --platform linux/amd64 \
  --push \
  -t "${BACKEND_REPO}:${TAG}" \
  "${SCRIPT_DIR}/backend"

log "Building & pushing frontend image (tag: $TAG)..."
docker buildx build \
  --platform linux/amd64 \
  --push \
  -t "${FRONTEND_REPO}:${TAG}" \
  "${SCRIPT_DIR}/frontend"

# ── Force new ECS deployments ─────────────────────────────────────────────────
for SERVICE in frontend backend worker; do
  log "Deploying ECS service: $SERVICE..."
  aws ecs update-service \
    --region "$AWS_REGION" \
    --cluster "$CLUSTER" \
    --service "gmra-calculator-${SERVICE}" \
    --force-new-deployment \
    --query "service.{name:serviceName,status:status,desired:desiredCount}" \
    --output table
done

# ── Wait for stability ────────────────────────────────────────────────────────
log "Waiting for services to stabilize..."
for SERVICE in frontend backend worker; do
  log "  Waiting on gmra-calculator-${SERVICE}..."
  aws ecs wait services-stable \
    --region "$AWS_REGION" \
    --cluster "$CLUSTER" \
    --services "gmra-calculator-${SERVICE}"
  log "  gmra-calculator-${SERVICE} is stable."
done

log "Deploy complete."
