#!/bin/bash
# Test VEVO bypass with iOS client and PO Token
POT_DATA=$(curl -s -X POST http://127.0.0.1:4416/get_pot)
POT=$(echo $POT_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('poToken') or data.get('po_token') or data.get('potoken') or '')")
VISITOR=$(echo $POT_DATA | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('contentBinding') or data.get('visitor_data') or data.get('visit_identifier') or data.get('visitorData') or '')")

echo "Using POT: ${POT:0:10}..."
echo "Using Visitor: $VISITOR"

if command -v docker &> /dev/null; then
    docker compose exec app yt-dlp \
      --extractor-args "youtube:player_client=ios;po_token=ios+$POT,web+$POT;visitor_data=$VISITOR" \
      --no-playlist --skip-download --list-formats \
      "https://www.youtube.com/watch?v=7LPOwfDN4d4"
else
    yt-dlp \
      --extractor-args "youtube:player_client=ios;po_token=ios+$POT,web+$POT;visitor_data=$VISITOR" \
      --no-playlist --skip-download --list-formats \
      "https://www.youtube.com/watch?v=7LPOwfDN4d4"
fi
