#!/bin/bash

if [ "$1" ]; then
    WS_PATH="$1"
else
    # If not, fall back to the WS_PATH environment variable
    WS_PATH="${WS_PATH:-ws}"
fi

/usr/local/share/desktop-init.sh
node playwright/playwright_server.ts $WS_PATH
