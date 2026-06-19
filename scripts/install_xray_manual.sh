#!/bin/sh
# Ручная установка Xray на Linux (без install-release.sh с GitHub).
# Использование: sudo sh scripts/install_xray_manual.sh
# С прокси: sudo HTTPS_PROXY=http://user:pass@host:3128 sh scripts/install_xray_manual.sh

set -e

XRAY_VERSION="${XRAY_VERSION:-26.2.2}"
INSTALL_DIR="${INSTALL_DIR:-/usr/local/bin}"
CONFIG_DIR="${CONFIG_DIR:-/usr/local/etc/xray}"
SERVICE_USER="${SERVICE_USER:-nobody}"

arch="$(uname -m)"
case "$arch" in
  x86_64|amd64) XRAY_ARCH="64" ;;
  aarch64|arm64) XRAY_ARCH="arm64-v8a" ;;
  armv7l|armv6l) XRAY_ARCH="arm32-v7a" ;;
  *)
    echo "Unsupported arch: $arch"
    exit 1
  ;;
esac

ZIP_NAME="Xray-linux-${XRAY_ARCH}.zip"
URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/${ZIP_NAME}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Downloading Xray v${XRAY_VERSION} (${ZIP_NAME})..."
if command -v curl >/dev/null 2>&1; then
  curl -fL --retry 3 --connect-timeout 30 -o "$TMP_DIR/$ZIP_NAME" "$URL"
elif command -v wget >/dev/null 2>&1; then
  wget -q -O "$TMP_DIR/$ZIP_NAME" "$URL"
else
  echo "Need curl or wget"
  exit 1
fi

command -v unzip >/dev/null 2>&1 || {
  echo "Install unzip: apt install unzip / yum install unzip"
  exit 1
}

unzip -q "$TMP_DIR/$ZIP_NAME" -d "$TMP_DIR"
install -m 755 "$TMP_DIR/xray" "$INSTALL_DIR/xray"
mkdir -p "$CONFIG_DIR"
mkdir -p /var/log/xray
chown "$SERVICE_USER:$SERVICE_USER" /var/log/xray 2>/dev/null || true

if [ ! -f /etc/systemd/system/xray.service ]; then
  RUN_USER="root"
  RUN_GROUP="root"
  if id nobody >/dev/null 2>&1; then
    RUN_USER="nobody"
    if getent group nogroup >/dev/null 2>&1; then
      RUN_GROUP="nogroup"
    elif getent group nobody >/dev/null 2>&1; then
      RUN_GROUP="nobody"
    else
      RUN_USER="root"
      RUN_GROUP="root"
    fi
  fi
  cat >/etc/systemd/system/xray.service <<EOF
[Unit]
Description=Xray Service
After=network.target nss-lookup.target

[Service]
User=$RUN_USER
Group=$RUN_GROUP
ExecStart=$INSTALL_DIR/xray run -config $CONFIG_DIR/config.json
Restart=on-failure
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
fi

"$INSTALL_DIR/xray" version
echo "OK: $INSTALL_DIR/xray"
echo "Config: $CONFIG_DIR/config.json"
echo "Enable: systemctl enable --now xray"
