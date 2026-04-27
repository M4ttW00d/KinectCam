#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; NC='\033[0m'
info() { echo -e "${GREEN}[KinectCam]${NC} $*"; }
die()  { echo -e "${RED}[KinectCam] ERROR:${NC} $*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Run with sudo: sudo bash uninstall.sh"
SERVICE_NAME="kinectcam"

info "Stopping and disabling service..."
systemctl stop "$SERVICE_NAME"    2>/dev/null || true
systemctl disable "$SERVICE_NAME" 2>/dev/null || true
rm -f /etc/systemd/system/kinectcam.service
systemctl daemon-reload

info "Removing udev rules..."
rm -f /etc/udev/rules.d/99-kinect.rules
udevadm control --reload-rules

info "Removing v4l2loopback config..."
rm -f /etc/modprobe.d/kinectcam.conf
sed -i '/^v4l2loopback$/d' /etc/modules 2>/dev/null || true

info "Removing application menu entries..."
rm -f /usr/local/share/applications/kinectcam-overlay.desktop

info "Removing application files..."
rm -rf /opt/kinectcam

info "Removing kinectcam system user..."
userdel kinectcam 2>/dev/null || true

echo ""
echo -e "${GREEN}KinectCam uninstalled.${NC}"
