#!/usr/bin/env bash
set -e
# deb passes "remove"/"purge" on uninstall; rpm passes 0
if [ "$1" = "remove" ] || [ "$1" = "purge" ] || [ "$1" = "0" ]; then
    userdel kinectcam 2>/dev/null || true
    rm -rf /opt/kinectcam
    rm -f /etc/modprobe.d/kinectcam.conf
    rm -f /etc/modules-load.d/kinectcam.conf
    modprobe -r v4l2loopback 2>/dev/null || true
    systemctl daemon-reload 2>/dev/null || true
fi
