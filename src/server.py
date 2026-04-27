import asyncio
import logging

import cv2
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path

import config

logger = logging.getLogger(__name__)

app = FastAPI(title="KinectCam")

# Populated by main.py before server starts
kinect = None
vcam = None


class TiltRequest(BaseModel):
    angle: float


class LEDRequest(BaseModel):
    led: str


class MirrorRequest(BaseModel):
    mirror: bool


@app.get("/api/state")
async def get_state():
    return kinect.get_state()


@app.post("/api/tilt")
async def set_tilt(req: TiltRequest):
    if not -30 <= req.angle <= 30:
        raise HTTPException(status_code=400, detail="Angle must be between -30 and 30")
    kinect.set_tilt(req.angle)
    config.save(kinect.get_state())
    return {"status": "ok", "angle": req.angle}


@app.post("/api/led")
async def set_led(req: LEDRequest):
    valid = ["off", "green", "red", "yellow", "blink_green", "blink_red_yellow"]
    if req.led not in valid:
        raise HTTPException(status_code=400, detail=f"LED must be one of {valid}")
    kinect.set_led(req.led)
    config.save(kinect.get_state())
    return {"status": "ok", "led": req.led}


@app.post("/api/mirror")
async def set_mirror(req: MirrorRequest):
    kinect.set_mirror(req.mirror)
    config.save(kinect.get_state())
    return {"status": "ok", "mirror": req.mirror}


def _make_placeholder_jpeg() -> bytes:
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, "No Kinect detected", (140, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 80, 80), 2)
    cv2.putText(img, "Check USB connection", (150, 270),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 60, 60), 1)
    _, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


@app.get("/stream")
async def video_stream():
    async def generate():
        placeholder = _make_placeholder_jpeg()
        while True:
            frame = kinect.get_frame()
            if frame is not None:
                bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                _, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
                jpeg = buf.tobytes()
            else:
                jpeg = placeholder
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            await asyncio.sleep(1 / 30)

    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
