#!/bin/bash
set -euo pipefail

WORKSPACE=$(terraform workspace show)
VALID_WORKSPACES=("client" "personal")

if [[ ! " ${VALID_WORKSPACES[*]} " =~ " ${WORKSPACE} " ]]; then
  echo "Error: unknown workspace '${WORKSPACE}'. Valid: ${VALID_WORKSPACES[*]}"
  exit 1
fi

TFVARS_FILE="${WORKSPACE}.tfvars"

if [[ ! -f "$TFVARS_FILE" ]]; then
  echo "Error: ${TFVARS_FILE} not found. Copy ${WORKSPACE}.tfvars.example and fill in values."
  exit 1
fi

echo "Deploying workspace: ${WORKSPACE}"
terraform apply -var-file="${TFVARS_FILE}" "$@"
