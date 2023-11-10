#!/bin/bash

USERNAME=${1:-"automatic"}
VNC_PASSWORD=${2:-"vscode"}
INSTALL_NOVNC=${3:-"true"}
VNC_PORT="${4:-5901}"
NOVNC_PORT="${5:-6080}"

NOVNC_VERSION=1.2.0
WEBSOCKETIFY_VERSION=0.10.0

mkdir -p /usr/local/novnc
curl -sSL https://github.com/novnc/noVNC/archive/v${NOVNC_VERSION}.zip -o /tmp/novnc-install.zip
unzip /tmp/novnc-install.zip -d /usr/local/novnc
cp /usr/local/novnc/noVNC-${NOVNC_VERSION}/vnc.html /usr/local/novnc/noVNC-${NOVNC_VERSION}/index.html
curl -sSL https://github.com/novnc/websockify/archive/v${WEBSOCKETIFY_VERSION}.zip -o /tmp/websockify-install.zip
unzip /tmp/websockify-install.zip -d /usr/local/novnc
ln -s /usr/local/novnc/websockify-${WEBSOCKETIFY_VERSION} /usr/local/novnc/noVNC-${NOVNC_VERSION}/utils/websockify
rm -f /tmp/websockify-install.zip /tmp/novnc-install.zip

# Install noVNC dependencies and use them.
if ! dpkg -s python3-minimal python3-numpy > /dev/null 2>&1; then
    apt-get -y install --no-install-recommends python3-minimal python3-numpy
fi
sed -i -E 's/^python /python3 /' /usr/local/novnc/websockify-${WEBSOCKETIFY_VERSION}/run