#!/usr/bin/env bash
set -e
# deb passes "remove" on uninstall; rpm passes 0
if [ "$1" = "remove" ] || [ "$1" = "0" ]; then
    systemctl stop kinectcam 2>/dev/null || true
    systemctl disable kinectcam 2>/dev/null || true
fi
