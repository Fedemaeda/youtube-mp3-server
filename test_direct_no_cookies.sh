#!/bin/bash
POT_DATA=$(curl -s -X POST http://127.0.0.1:4416/get_pot)
POT=$(echo $POT_DATA | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("poToken") or "")')
VISITOR=$(echo $POT_DATA | python3 -c 'import sys, json; data=json.load(sys.stdin); print(data.get("contentBinding") or "")')
echo "Using Token: $POT"
docker compose exec app yt-dlp \
  --extractor-args "youtube:player_client=ios,mweb;po_token=ios+$POT,mweb+$POT;visitor_data=$VISITOR" \
  --list-formats "https://www.youtube.com/watch?v=D64Hq6njZyo"
