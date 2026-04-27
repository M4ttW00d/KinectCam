# KinectCam

Use an **Xbox 360 Kinect** as a virtual webcam on Linux — with remote tilt, LED, and mirror control.

KinectCam creates a virtual V4L2 camera device (`/dev/video36`) that any app (Teams, Meet, OBS, etc.) can select as "KinectCam". A local web UI and a GTK desktop overlay let you adjust the motorised tilt in real time. A browser extension puts the same controls one click away from any tab.

---

## Requirements

- **Hardware:** Xbox 360 Kinect (model 1414 or 1473)
- **OS:** Ubuntu 22.04 or 24.04 LTS (other systemd-based distros likely work)
- **Kernel:** v4l2loopback support (installed automatically)

---

## Installation

```bash
git clone https://github.com/M4ttW00d/KinectCam.git
cd KinectCam
sudo bash install.sh
```

The installer will:

1. Install system packages (`libfreenect`, `v4l2loopback`, `ffmpeg`, Python 3)
2. Load the `v4l2loopback` kernel module and persist it across reboots
3. Install udev rules so the Kinect is accessible without root
4. Create a dedicated `kinectcam` system user and add it to the `video` group
5. Create a Python virtualenv and install all dependencies
6. Register and start a **systemd service** (`kinectcam`)
7. Add the **tilt overlay** to your applications menu

---

## Usage

### Web UI

Open **http://localhost:36000** in your browser.

| Section | What it does |
|---------|-------------|
| Preview | Live MJPEG stream from the Kinect |
| Tilt | Up / Down buttons or drag the slider (−30° to +30°) |
| LED | Choose the Kinect's indicator colour / blink mode |
| Mirror | Flip the image horizontally |

### Desktop overlay

Launch **KinectCam Overlay** from your applications menu. A small floating window provides **Up**, **Down**, and **Level** buttons for quick tilt adjustments without opening the browser.

### Browser extension

Load the `extension/` folder as an unpacked extension in Chrome/Edge:

1. Go to `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `extension/` folder

The extension popup gives you the same tilt controls from any tab.

### Virtual camera

Select **KinectCam** (or `/dev/video36`) in any video-conferencing app or OBS.

---

## Service management

```bash
# Status and logs
sudo service kinectcam status
journalctl -u kinectcam -f

# Restart / stop
sudo service kinectcam restart
sudo service kinectcam stop
```

---

## Uninstall

```bash
sudo bash /opt/kinectcam/uninstall.sh
```

---

## How it works

```
Kinect USB
   │
   ▼
freenect (libfreenect)          – reads raw RGB frames in a background thread
   │
   ▼
KinectManager (src/kinect.py)   – thread-safe frame store, tilt/LED control, auto-reconnect
   │
   ▼
VirtualCamera (src/virtual_camera.py)  – pipes frames to ffmpeg → /dev/video36 (v4l2loopback)
   │
   ▼
/dev/video36                    – appears as a standard webcam to any app
```

The FastAPI server (`src/server.py`) runs alongside the frame pump and exposes:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stream` | GET | MJPEG video stream |
| `/api/state` | GET | Current tilt, LED, mirror, connection status |
| `/api/tilt` | POST | Set tilt angle |
| `/api/led` | POST | Set LED mode |
| `/api/mirror` | POST | Toggle mirror |

Settings are persisted to `settings.json` and restored on startup.

---

## Troubleshooting

**Kinect not detected**
- Check `lsusb` for `045e:02ae` / `045e:02b0`
- Make sure you're in the `video` group: `groups $USER`
- Reconnect the USB cable and restart the service

**`/dev/video36` not available**
```bash
sudo modprobe v4l2loopback devices=1 video_nr=36 card_label=KinectCam exclusive_caps=1
```

**Service won't start**
```bash
journalctl -u kinectcam -n 50
```

---

## License

MIT — see [LICENSE](LICENSE).
