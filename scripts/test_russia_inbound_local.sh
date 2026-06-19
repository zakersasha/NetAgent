#!/bin/sh
# Тест inbound на России с loopback (порт из /usr/local/etc/xray/config.json).
# sudo sh scripts/test_russia_inbound_local.sh

set -e

CONFIG="${CONFIG:-/usr/local/etc/xray/config.json}"
PBK="${PBK:-j-iuguAzBEJ4-u76nVncqDxBipKnsPgGkBOunpoYBXA}"
UUID="${UUID:-822c54b6-4fae-4043-9774-70cd879c283f}"

if [ ! -f "$CONFIG" ]; then
  echo "Config not found: $CONFIG"
  exit 1
fi

PORT=$(grep -m1 '"port"' "$CONFIG" | grep -oE '[0-9]+')
if [ -z "$PORT" ]; then
  echo "Could not read port from $CONFIG"
  exit 1
fi

if ! systemctl is-active --quiet xray; then
  echo "xray service is not running. Start: systemctl start xray"
  exit 1
fi

if ! ss -lntp | grep -q ":${PORT}"; then
  echo "Nothing listens on port ${PORT}. Check: ss -lntp | grep ${PORT}"
  exit 1
fi

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

echo "Testing inbound on 127.0.0.1:${PORT} (from $CONFIG) ..."
CLIENT_PID=""
cleanup() {
  [ -n "$CLIENT_PID" ] && kill "$CLIENT_PID" 2>/dev/null || true
  rm -rf "$TMP"
}
trap cleanup EXIT

xray run -config "$TMP/client.json" >/tmp/xray-client-test.log 2>&1 &
CLIENT_PID=$!
sleep 2

if curl -sf --max-time 8 -x socks5h://127.0.0.1:10808 https://ifconfig.me; then
  echo ""
  echo "OK: inbound на порту ${PORT} работает. Если iPhone не работает — клиент/Streisand."
else
  echo "FAIL: curl через SOCKS не прошёл."
  echo "--- client log ---"
  tail -20 /tmp/xray-client-test.log
  echo "--- server (last 15) ---"
  journalctl -u xray -n 15 --no-pager
fi
