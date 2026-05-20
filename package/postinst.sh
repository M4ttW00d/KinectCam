#!/usr/bin/env bash
set -e

NOLOGIN=$(command -v nologin 2>/dev/null || echo /usr/sbin/nologin)
if ! id kinectcam &>/dev/null; then
    useradd --system --no-create-home --shell "$NOLOGIN" kinectcam
fi
usermod -aG video kinectcam

cat > /etc/modprobe.d/kinectcam.conf <<'EOF'
options v4l2loopback devices=1 video_nr=36 card_label=KinectCam exclusive_caps=1
EOF
echo "v4l2loopback" > /etc/modules-load.d/kinectcam.conf
modprobe v4l2loopback devices=1 video_nr=36 card_label=KinectCam exclusive_caps=1 2>/dev/null || true

python3 -m venv --system-site-packages /opt/kinectcam/venv
/opt/kinectcam/venv/bin/pip install --quiet --no-cache-dir \
    freenect \
    -r /opt/kinectcam/requirements.txt

chown -R kinectcam:kinectcam /opt/kinectcam

udevadm control --reload-rules
udevadm trigger

systemctl daemon-reload
systemctl enable kinectcam
systemctl restart kinectcam || true
