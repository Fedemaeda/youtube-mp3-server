#!/bin/bash
# Test YouTube bypass with PO Token and cookies
POT_DATA=$(curl -s -X POST http://127.0.0.1:4416/get_pot)
POT=$(echo $POT_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('poToken') or data.get('po_token') or data.get('potoken') or '')")
VISITOR=$(echo $POT_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('contentBinding') or data.get('visitor_data') or data.get('visit_identifier') or data.get('visitorData') or '')")

if [ -z "$POT" ]; then
    echo "FAILED to get PO Token"
    echo "Raw response: $POT_DATA"
    exit 1
fi

echo "Using Token: ${POT:0:10}..."
echo "Using Visitor: $VISITOR"

if command -v docker &> /dev/null; then
    docker compose exec app yt-dlp \
      --proxy socks5h://127.0.0.1:40000 \
      --cookies /app/cookies.txt \
      --extractor-args "youtube:player_client=ios,mweb,android,web;po_token=web+$POT,mweb+$POT,ios+$POT,android+$POT;visitor_data=$VISITOR" \
      --list-formats "https://www.youtube.com/watch?v=D64Hq6njZyo"
else
    yt-dlp \
      --proxy socks5h://127.0.0.1:40000 \
      --cookies cookies.txt \
      --extractor-args "youtube:player_client=ios,mweb,android,web;po_token=web+$POT,mweb+$POT,ios+$POT,android+$POT;visitor_data=$VISITOR" \
      --list-formats "https://www.youtube.com/watch?v=D64Hq6njZyo"
fi
