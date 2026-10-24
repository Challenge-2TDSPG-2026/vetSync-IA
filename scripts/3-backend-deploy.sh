#!/usr/bin/env bash
set -euo pipefail

GROUP="rg-vetsync"
APP_NAME="app-vetsync-ia"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
TEMP_DIR=$(mktemp -d)
ZIP_PATH="$TEMP_DIR/vetsync-ia.zip"
trap 'rm -rf -- "$TEMP_DIR"' EXIT

command -v az >/dev/null 2>&1 || { echo "Azure CLI (az) is required." >&2; exit 1; }
command -v zip >/dev/null 2>&1 || { echo "zip is required." >&2; exit 1; }
if ! az webapp show --resource-group "$GROUP" --name "$APP_NAME" >/dev/null 2>&1; then
    echo "App Service $APP_NAME not found. Run scripts/1-system.sh first." >&2
    exit 1
fi
if [[ ! -f "$APP_ROOT/main.py" || ! -f "$APP_ROOT/requirements.txt" ]]; then
    echo "Expected main.py and requirements.txt at $APP_ROOT." >&2
    exit 1
fi

(
    cd "$APP_ROOT"
    zip -qr "$ZIP_PATH" . \
        -x '.git' '.git/*' '.venv' '.venv/*' '.env' \
        -x '.pytest_cache' '.pytest_cache/*' '__pycache__' '__pycache__/*' '*/__pycache__/*' \
        -x '*.pyc' 'dev_database.db' \
        -x '.vscode' '.vscode/*' '.agents' '.agents/*' '.codex' '.codex/*' '.aws' '.aws/*'
)

az webapp config appsettings set --resource-group "$GROUP" --name "$APP_NAME" \
    --settings "SCM_DO_BUILD_DURING_DEPLOYMENT=true" \
        "WEBSITE_HEALTHCHECK_MAXPINGFAILURES=10" --output none
echo "Deploying FastAPI source to https://$APP_NAME.azurewebsites.net ..."
az webapp deploy --resource-group "$GROUP" --name "$APP_NAME" \
    --src-path "$ZIP_PATH" --type zip --output none

HEALTH_URL="https://$APP_NAME.azurewebsites.net/health"
echo "Waiting for $HEALTH_URL ..."
for attempt in {1..30}; do
    if curl --fail --silent --show-error --max-time 20 "$HEALTH_URL" >/dev/null; then
        echo "FastAPI IA is responding at https://$APP_NAME.azurewebsites.net"
        exit 0
    fi
    echo "Health check attempt $attempt/30 failed; retrying in 10 seconds..."
    sleep 10
done
echo "Deployment completed, but /health did not become healthy." >&2
echo "Inspect logs with: az webapp log tail --resource-group $GROUP --name $APP_NAME" >&2
exit 1
