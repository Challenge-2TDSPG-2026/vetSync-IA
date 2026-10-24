#!/usr/bin/env bash
set -euo pipefail

GROUP="rg-vetsync"
KEYVAULT_NAME="kv-vetsync-rm563197"
APP_NAME="app-vetsync-ia"
APP_ENV="${APP_ENV:-}"
GEMINI_API_KEY="${GEMINI_API_KEY:-}"
JAVA_API_BASE_URL="${JAVA_API_BASE_URL:-https://app-vetsync-rm563197.azurewebsites.net}"
ORACLE_DB_URL="${ORACLE_DB_URL:-}"

prompt_setting() {
    local name="$1" prompt="$2" secret="${3:-false}" value="${!1:-}"
    if [[ -z "$value" ]]; then
        if [[ "$secret" == "true" ]]; then
            read -r -s -p "$prompt: " value
            echo
        else
            read -r -p "$prompt: " value
        fi
    fi
    printf -v "$name" '%s' "$value"
}

if ! az webapp show --resource-group "$GROUP" --name "$APP_NAME" >/dev/null 2>&1; then
    echo "App Service $APP_NAME not found. Run scripts/1-system.sh first." >&2
    exit 1
fi
if ! az keyvault show --resource-group "$GROUP" --name "$KEYVAULT_NAME" >/dev/null 2>&1; then
    echo "Key Vault $KEYVAULT_NAME not found. Run scripts/1-system.sh first." >&2
    exit 1
fi

prompt_setting APP_ENV "APP_ENV [prod]"
APP_ENV="${APP_ENV:-prod}"
if [[ "$APP_ENV" != "prod" ]]; then
    echo "APP_ENV must be 'prod'; dev mode uses local SQLite and development authentication." >&2
    exit 1
fi
prompt_setting GEMINI_API_KEY "GEMINI_API_KEY" true
prompt_setting JAVA_API_BASE_URL "JAVA_API_BASE_URL"
prompt_setting ORACLE_DB_URL "ORACLE_DB_URL" true
if [[ -z "$GEMINI_API_KEY" || -z "$ORACLE_DB_URL" ]]; then
    echo "GEMINI_API_KEY and ORACLE_DB_URL are required to configure the production IA." >&2
    exit 1
fi
if [[ ! "$JAVA_API_BASE_URL" =~ ^https?://[^/]+/?$ ]]; then
    echo "JAVA_API_BASE_URL must be an absolute HTTP(S) origin without a path." >&2
    exit 1
fi
if ! az keyvault secret show --vault-name "$KEYVAULT_NAME" --name "jwt-secret" --query id --output none; then
    echo "Java JWT secret not found in Key Vault; configure the Java backend first." >&2
    exit 1
fi

az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "ia-gemini-api-key" \
    --value "$GEMINI_API_KEY" --output none
az keyvault secret set --vault-name "$KEYVAULT_NAME" --name "ia-oracle-db-url" \
    --value "$ORACLE_DB_URL" --output none

az webapp identity assign --resource-group "$GROUP" --name "$APP_NAME" --output none
APP_PRINCIPAL_ID=$(az webapp identity show --resource-group "$GROUP" \
    --name "$APP_NAME" --query principalId --output tsv)
KEYVAULT_ID=$(az keyvault show --resource-group "$GROUP" \
    --name "$KEYVAULT_NAME" --query id --output tsv)
if ! az role assignment list --assignee-object-id "$APP_PRINCIPAL_ID" \
    --scope "$KEYVAULT_ID" --role "Key Vault Secrets User" \
    --query "[0].id" --output tsv | grep -q .; then
    az role assignment create --assignee-object-id "$APP_PRINCIPAL_ID" \
        --assignee-principal-type ServicePrincipal --role "Key Vault Secrets User" \
        --scope "$KEYVAULT_ID" --output none
fi

az webapp config appsettings set --resource-group "$GROUP" --name "$APP_NAME" \
    --settings \
        "APP_ENV=$APP_ENV" \
        "AUTH_JWT_SECRET=@Microsoft.KeyVault(VaultName=$KEYVAULT_NAME;SecretName=jwt-secret)" \
        "GEMINI_API_KEY=@Microsoft.KeyVault(VaultName=$KEYVAULT_NAME;SecretName=ia-gemini-api-key)" \
        "JAVA_API_BASE_URL=$JAVA_API_BASE_URL" \
        "ORACLE_DB_URL=@Microsoft.KeyVault(VaultName=$KEYVAULT_NAME;SecretName=ia-oracle-db-url)" \
    --output none
unset GEMINI_API_KEY ORACLE_DB_URL
echo "IA settings stored in Key Vault and connected to $APP_NAME. Java and IA now share the JWT secret reference. Secret values were not printed."
