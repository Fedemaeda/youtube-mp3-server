#!/bin/bash
# Script de prueba exhaustiva con PROXY y PO Token
export HTTP_PROXY=socks5h://127.0.0.1:40000
export HTTPS_PROXY=socks5h://127.0.0.1:40000

POT_DATA=$(curl -s -X POST http://127.0.0.1:4416/get_pot)
POT=$(echo "$POT_DATA" | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("poToken") or "")')
VISITOR=$(echo "$POT_DATA" | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("contentBinding") or "")')

if [ -z "$POT" ]; then
    echo "ERROR: No se pudo obtener PO Token"
    exit 1
fi

URL="https://www.youtube.com/watch?v=P2JNhprE9Ho"

test_client() {
  local client=$1
  echo "------------------------------------------------"
  echo "TESTING: $client (with Proxy and POT)"
  echo "------------------------------------------------"
  docker compose exec -T app yt-dlp \
    --proxy socks5h://127.0.0.1:40000 \
    --extractor-args "youtube:player_client=$client;po_token=$client+$POT;visitor_data=$VISITOR" \
    --simulate \
    "$URL"
}

test_client "android"
test_client "ios"
test_client "tv"
test_client "mweb"
test_client "web_safari"
