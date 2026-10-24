#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
JAVA_DIR="${1:-$PROJECT_DIR/../../services/java}"
MIGRATIONS_DIR="$JAVA_DIR/src/main/resources/db/migration"
OUTPUT_FILE="$SCRIPT_DIR/Database/script_bd.sql"

if [[ ! -d "$MIGRATIONS_DIR" ]]; then
    echo "Migration directory not found: $MIGRATIONS_DIR" >&2
    echo "Usage: $0 /path/to/vetSync-java" >&2
    exit 1
fi

mkdir -p "$(dirname -- "$OUTPUT_FILE")"
TEMP_FILE=$(mktemp)
trap 'rm -f -- "$TEMP_FILE"' EXIT
{
    printf '%s\n' '-- VetSync - Oracle DDL and schema evolution script'
    printf '%s\n' '-- Generated from the versioned Flyway migrations in vetSync-java.'
    printf '%s\n' '-- Intended for academic evidence or manual execution on an EMPTY Oracle schema.'
    printf '%s\n' '-- Normal application deployment must let Flyway execute the original migration files.'
    printf '%s\n\n' '-- Do not run this file before Flyway in the same schema.'
    find "$MIGRATIONS_DIR" -maxdepth 1 -type f -name 'V*.sql' -print0 \
        | sort -z -V \
        | while IFS= read -r -d '' migration; do
            printf '\n-- ============================================================================\n'
            printf '%s\n' "-- $(basename "$migration")"
            printf '%s\n\n' '-- ============================================================================'
            sed -e '$a\' "$migration"
        done
} > "$TEMP_FILE"

mv "$TEMP_FILE" "$OUTPUT_FILE"
trap - EXIT
echo "Oracle DDL synchronized at $OUTPUT_FILE"
