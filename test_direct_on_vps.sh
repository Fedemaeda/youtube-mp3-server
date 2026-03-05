#!/bin/bash
# Desactivamos el proxy para esta prueba
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY

# Obtenemos el PO Token de bgutil
POT_DATA=$(curl -s -X POST http://127.0.0.1:4416/get_pot)
POT=$(echo "$POT_DATA" | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("poToken") or "")')
VISITOR=$(echo "$POT_DATA" | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("contentBinding") or "")')

if [ -z "$POT" ]; then
    echo "ERROR: No se pudo obtener PO Token"
    exit 1
fi

echo "Testing direct (no proxy) with android + PO token..."
docker compose exec -T app yt-dlp \
  --extractor-args "youtube:player_client=android;po_token=android+$POT;visitor_data=$VISITOR" \
  --simulate \
  "https://www.youtube.com/watch?v=P2JNhprE9Ho"
