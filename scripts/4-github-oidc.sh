#!/usr/bin/env bash
set -euo pipefail

GROUP="rg-vetsync"
DEPLOY_IDENTITY_NAME="id-vetsync-github"
GITHUB_REPOSITORY="Challenge-2TDSPG-2026/vetSync-IA"

command -v gh >/dev/null 2>&1 || { echo "GitHub CLI (gh) is required." >&2; exit 1; }
gh auth status >/dev/null
AZURE_CLIENT_ID=$(az identity show --resource-group "$GROUP" \
    --name "$DEPLOY_IDENTITY_NAME" --query clientId --output tsv)
AZURE_TENANT_ID=$(az account show --query tenantId --output tsv)
AZURE_SUBSCRIPTION_ID=$(az account show --query id --output tsv)
printf '%s' "$AZURE_CLIENT_ID" | gh secret set AZURE_CLIENT_ID --repo "$GITHUB_REPOSITORY"
printf '%s' "$AZURE_TENANT_ID" | gh secret set AZURE_TENANT_ID --repo "$GITHUB_REPOSITORY"
printf '%s' "$AZURE_SUBSCRIPTION_ID" | gh secret set AZURE_SUBSCRIPTION_ID --repo "$GITHUB_REPOSITORY"
echo "GitHub Actions OIDC identifiers configured in $GITHUB_REPOSITORY."
