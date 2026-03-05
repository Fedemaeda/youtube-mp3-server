#!/bin/bash
POT_DATA=$(curl -s -X POST http://127.0.0.1:4416/get_pot)
POT=$(echo $POT_DATA | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("poToken") or "")')
VISITOR=$(echo $POT_DATA | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("contentBinding") or "")')

if [ -z "$POT" ]; then
    echo "ERROR: No se pudo obtener PO Token"
    exit 1
fi

echo "Probando bypass con mweb para biJZvORqN9s..."
docker compose exec app yt-dlp \
  --proxy socks5h://127.0.0.1:40000 \
  --extractor-args "youtube:player_client=mweb,ios;po_token=mweb+$POT,ios+$POT;visitor_data=$VISITOR" \
  --list-formats "https://www.youtube.com/watch?v=biJZvORqN9s"
