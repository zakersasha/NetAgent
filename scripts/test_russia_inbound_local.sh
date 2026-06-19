#!/bin/sh
# Тест inbound на России с самого сервера (loopback).
# Запуск на 37.230.114.25: sudo sh scripts/test_russia_inbound_local.sh

set -e

PBK="${PBK:-j-iuguAzBEJ4-u76nVncqDxBipKnsPgGkBOunpoYBXA}"
UUID="${UUID:-822c54b6-4fae-4043-9774-70cd879c283f}"
PORT="${PORT:-2053}"

TMP=$(mktemp -d)
cat >"$TMP/client.json" <<EOF
{
  "log": { "loglevel": "warning" },
  "inbounds": [
    {
      "port": 10808,
      "listen": "127.0.0.1",
      "protocol": "socks",
      "settings": { "udp": true }
    }
  ],
  "outbounds": [
    {
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "127.0.0.1",
            "port": ${PORT},
            "users": [
              {
                "id": "${UUID}",
                "encryption": "none",
                "flow": "xtls-rprx-vision"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "serverName": "www.wikipedia.org",
          "publicKey": "${PBK}",
          "shortId": "6ba85179e30d4fc2",
          "fingerprint": "chrome"
        }
      }
    }
  ]
}
EOF

echo "Testing VLESS Reality to 127.0.0.1:${PORT} ..."
timeout 8 xray run -config "$TMP/client.json" &
XPID=$!
sleep 2
if curl -s --max-time 5 -x socks5h://127.0.0.1:10808 https://ifconfig.me; then
  echo ""
  echo "OK: inbound на этом сервере работает (проблема в клиенте/сети до сервера)."
else
  echo "FAIL: inbound не отвечает — проверьте config и systemctl status xray"
fi
kill "$XPID" 2>/dev/null || true
rm -rf "$TMP"
