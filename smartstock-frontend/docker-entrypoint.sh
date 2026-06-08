#!/bin/sh
set -e

ENV_FILE=/usr/share/nginx/html/env-config.js

echo "window.__ENV__ = {" > "$ENV_FILE"

# Write each VITE_ env var into the config
for var in $(env | grep -o '^VITE_[^=]*'); do
    value=$(eval echo "\$$var")
    echo "  \"$var\": \"$value\"," >> "$ENV_FILE"
done

# Always include VITE_API_URL with a default if not set
if ! grep -q '"VITE_API_URL"' "$ENV_FILE" 2>/dev/null; then
    echo '  "VITE_API_URL": "/api",' >> "$ENV_FILE"
fi

echo "};" >> "$ENV_FILE"

exec "$@"
