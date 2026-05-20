#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
VERSION="$(cat "$ROOT/VERSION" | tr -d '[:space:]')"
STAGING="$SCRIPT_DIR/staging"
DIST="$ROOT/dist"

echo "Building KinectCam v${VERSION} packages..."

# ── Staging ───────────────────────────────────────────────────────────────────
rm -rf "$STAGING"
mkdir -p \
    "$STAGING/opt/kinectcam/src" \
    "$STAGING/etc/udev/rules.d" \
    "$STAGING/lib/systemd/system" \
    "$STAGING/usr/local/share/applications"

cp -r "$ROOT/src/"* "$STAGING/opt/kinectcam/src/"
cp "$ROOT/requirements.txt" "$STAGING/opt/kinectcam/"
cp "$ROOT/udev/99-kinect.rules" "$STAGING/etc/udev/rules.d/"

cat > "$STAGING/lib/systemd/system/kinectcam.service" <<'EOF'
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

cat > "$STAGING/usr/local/share/applications/kinectcam-overlay.desktop" <<'EOF'
[Desktop Entry]
Name=KinectCam Overlay
Comment=KinectCam tilt controller
Exec=/opt/kinectcam/venv/bin/python /opt/kinectcam/src/overlay.py
Terminal=false
Type=Application
Categories=Utility;
EOF

mkdir -p "$DIST"

COMMON=(
    -s dir
    -C "$STAGING"
    --name kinectcam
    --version "$VERSION"
    --architecture amd64
    --description "Xbox 360 Kinect virtual webcam for Linux"
    --url "https://github.com/M4ttW00d/KinectCam"
    --maintainer "Matt Wood <mjw4545@hotmail.co.uk>"
    --license MIT
    --after-install "$SCRIPT_DIR/postinst.sh"
    --before-remove "$SCRIPT_DIR/prerm.sh"
    --after-remove  "$SCRIPT_DIR/postrm.sh"
    .
)

# ── .deb (Debian / Ubuntu) ────────────────────────────────────────────────────
echo "Building .deb..."
fpm "${COMMON[@]}" \
    -t deb \
    --depends "python3 (>= 3.10)" \
    --depends "python3-venv" \
    --depends "python3-gi" \
    --depends "python3-dev" \
    --depends "libfreenect-dev" \
    --depends "v4l2loopback-dkms" \
    --depends "v4l2loopback-utils" \
    --depends "ffmpeg" \
    --package "$DIST/kinectcam_${VERSION}_amd64.deb"

# ── .rpm (Fedora / RHEL) ─────────────────────────────────────────────────────
echo "Building .rpm..."
fpm "${COMMON[@]}" \
    -t rpm \
    --depends "python3 >= 3.10" \
    --depends "python3-gobject3" \
    --depends "python3-devel" \
    --depends "libfreenect" \
    --depends "libfreenect-devel" \
    --depends "v4l2loopback" \
    --depends "ffmpeg" \
    --package "$DIST/kinectcam_${VERSION}_x86_64.rpm"

echo ""
echo "Packages built in dist/:"
ls -lh "$DIST/"
