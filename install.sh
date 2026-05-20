#!/usr/bin/env bash
set -euo pipefail

# ── KinectCam installer ──────────────────────────────────────────────────────
# Supports: Ubuntu 22.04/24.04, Fedora 38+, Arch Linux

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[KinectCam]${NC} $*"; }
warn()  { echo -e "${YELLOW}[KinectCam]${NC} $*"; }
die()   { echo -e "${RED}[KinectCam] ERROR:${NC} $*" >&2; exit 1; }

# ── Must run as root ─────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || die "Run with sudo: sudo bash install.sh"

INSTALL_DIR="/opt/kinectcam"
SERVICE_USER="kinectcam"
SERVICE_NAME="kinectcam"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── 1. Detect package manager and install system packages ─────────────────────
if   command -v apt-get &>/dev/null; then PKG_MANAGER=apt
elif command -v dnf     &>/dev/null; then PKG_MANAGER=dnf
elif command -v pacman  &>/dev/null; then PKG_MANAGER=pacman
else die "No supported package manager found (apt, dnf, or pacman required)"
fi
info "Detected package manager: $PKG_MANAGER"
info "Installing system packages..."

case "$PKG_MANAGER" in
apt)
    _freenect_lib=libfreenect0.5
    apt-cache show libfreenect0.5t64 &>/dev/null 2>&1 && _freenect_lib=libfreenect0.5t64
    apt-get update -qq
    apt-get install -y \
        python3 python3-pip python3-dev python3-venv python3-gi \
        python3-numpy cython3 \
        libfreenect-dev "$_freenect_lib" \
        v4l2loopback-dkms v4l2loopback-utils \
        ffmpeg
    ;;
dnf)
    if ! dnf list available ffmpeg 2>/dev/null | grep -q ffmpeg; then
        info "Enabling RPM Fusion Free repository for ffmpeg..."
        dnf install -y \
            "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm" \
            2>/dev/null || warn "Could not enable RPM Fusion — ffmpeg install may fail"
    fi
    dnf install -y \
        python3 python3-pip python3-devel python3-gobject3 \
        python3-numpy python3-Cython \
        libfreenect libfreenect-devel \
        v4l2loopback \
        ffmpeg
    ;;
pacman)
    if ! modinfo v4l2loopback &>/dev/null 2>&1; then
        warn "v4l2loopback is not in the official Arch repos."
        warn "Install it from the AUR first:  yay -S v4l2loopback-dkms"
        warn "Then re-run this script."
        die "v4l2loopback not found"
    fi
    pacman -Sy --noconfirm \
        python python-pip python-gobject \
        python-numpy cython \
        libfreenect \
        ffmpeg
    ;;
esac

# ── 2. v4l2loopback kernel module ────────────────────────────────────────────
info "Configuring v4l2loopback kernel module..."

cat > /etc/modprobe.d/kinectcam.conf <<'EOF'
options v4l2loopback devices=1 video_nr=36 card_label=KinectCam exclusive_caps=1
EOF

if modprobe v4l2loopback devices=1 video_nr=36 card_label=KinectCam exclusive_caps=1 2>/dev/null; then
    info "v4l2loopback loaded — virtual camera at /dev/video36"
else
    warn "Could not load v4l2loopback now (may need a reboot). Will load on next boot."
fi

echo "v4l2loopback" > /etc/modules-load.d/kinectcam.conf

# ── 3. udev rules ────────────────────────────────────────────────────────────
info "Installing udev rules for Kinect USB access..."
cp "$SCRIPT_DIR/udev/99-kinect.rules" /etc/udev/rules.d/
udevadm control --reload-rules
udevadm trigger

# ── 4. Create kinectcam system user ──────────────────────────────────────────
info "Creating system user '$SERVICE_USER'..."
NOLOGIN=$(command -v nologin 2>/dev/null || echo /usr/sbin/nologin)
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --no-create-home --shell "$NOLOGIN" "$SERVICE_USER"
fi
usermod -aG video "$SERVICE_USER"

# ── 5. Copy application files ────────────────────────────────────────────────
info "Installing application to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"
cp -r "$SCRIPT_DIR/." "$INSTALL_DIR/"
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# ── 6. Python virtual environment ────────────────────────────────────────────
info "Creating Python virtual environment..."
python3 -m venv --system-site-packages "$INSTALL_DIR/venv"

info "Installing Python dependencies (freenect will compile from source, takes ~1 min)..."
"$INSTALL_DIR/venv/bin/pip" install \
    --quiet \
    --no-cache-dir \
    freenect \
    -r "$INSTALL_DIR/requirements.txt"

# ── 7. systemd service ───────────────────────────────────────────────────────
info "Installing systemd service..."
cat > /etc/systemd/system/kinectcam.service <<'EOF'
[Unit]
Description=KinectCam - Xbox 360 Kinect virtual webcam
After=network.target systemd-modules-load.service

[Service]
Type=simple
User=kinectcam
WorkingDirectory=/opt/kinectcam
ExecStart=/opt/kinectcam/venv/bin/python src/main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME" || warn "Service start failed — the Kinect may not be plugged in yet."

# ── 8. Overlay application menu entry ───────────────────────────────────────
info "Installing overlay application menu entry..."
APPS_DIR="/usr/local/share/applications"
mkdir -p "$APPS_DIR"

cat > "$APPS_DIR/kinectcam-overlay.desktop" <<EOF
[Desktop Entry]
Name=KinectCam Overlay
Comment=KinectCam tilt controller
Exec=${INSTALL_DIR}/venv/bin/python ${INSTALL_DIR}/src/overlay.py
Terminal=false
Type=Application
Categories=Utility;
EOF

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  KinectCam installed successfully!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  GUI:           http://localhost:36000"
echo "  Virtual cam:   /dev/video36  (select 'KinectCam' in Teams/Meet)"
echo ""
echo "  Service:       sudo service $SERVICE_NAME status"
echo "  Logs:          journalctl -u $SERVICE_NAME -f"
echo "  Uninstall:     sudo bash $INSTALL_DIR/uninstall.sh"
echo ""
