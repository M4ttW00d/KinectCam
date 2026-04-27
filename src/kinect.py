import freenect
import threading
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

LED_OPTIONS = {
    "off": freenect.LED_OFF,
    "green": freenect.LED_GREEN,
    "red": freenect.LED_RED,
    "yellow": freenect.LED_YELLOW,
    "blink_green": freenect.LED_BLINK_GREEN,
    "blink_red_yellow": freenect.LED_BLINK_RED_YELLOW,
}

LED_LABELS = {v: k for k, v in LED_OPTIONS.items()}


FRAME_TIMEOUT = 5.0  # seconds without a frame before triggering reconnect


class KinectManager:
    def __init__(self):
        self._latest_frame = None
        self._frame_lock = threading.Lock()
        self._tilt_angle = 0.0
        self._led = freenect.LED_GREEN
        self._pending_tilt = None
        self._pending_led = None
        self._mirror = False
        self._running = False
        self._connected = False
        self._thread = None
        self._last_frame_time = 0.0

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run_with_retry, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _video_callback(self, dev, data, timestamp):
        with self._frame_lock:
            self._latest_frame = data.copy()
        self._last_frame_time = time.time()
        if not self._connected:
            self._connected = True
            logger.info("Kinect connected")

    def _body_callback(self, dev, ctx):
        if not self._running:
            raise freenect.Kill

        if self._connected and time.time() - self._last_frame_time > FRAME_TIMEOUT:
            logger.warning("No frames received for %.0fs — triggering reconnect", FRAME_TIMEOUT)
            raise freenect.Kill

        if self._pending_tilt is not None:
            try:
                freenect.set_tilt_degs(dev, self._pending_tilt)
                freenect.update_tilt_state(dev)
                self._tilt_angle = self._pending_tilt
            except Exception as e:
                logger.warning(f"Tilt set failed: {e}")
            self._pending_tilt = None

        if self._pending_led is not None:
            try:
                freenect.set_led(dev, self._pending_led)
                self._led = self._pending_led
            except Exception as e:
                logger.warning(f"LED set failed: {e}")
            self._pending_led = None

    def _run_with_retry(self):
        while self._running:
            self._last_frame_time = time.time()
            try:
                freenect.runloop(
                    video=self._video_callback,
                    body=self._body_callback,
                )
            except Exception as e:
                logger.error(f"Kinect runloop error: {e}")
            finally:
                self._connected = False
                with self._frame_lock:
                    self._latest_frame = None

            if self._running:
                logger.info("Kinect disconnected, retrying in 3s...")
                time.sleep(3)

    def get_frame(self):
        with self._frame_lock:
            if self._latest_frame is None:
                return None
            frame = self._latest_frame.copy()
        if self._mirror:
            frame = np.fliplr(frame).copy()
        return frame

    def set_tilt(self, angle: float):
        self._pending_tilt = max(-30.0, min(30.0, float(angle)))

    def set_led(self, name: str):
        if name in LED_OPTIONS:
            self._pending_led = LED_OPTIONS[name]

    def set_mirror(self, mirror: bool):
        self._mirror = bool(mirror)

    def get_state(self) -> dict:
        return {
            "connected": self._connected,
            "tilt": self._tilt_angle,
            "led": LED_LABELS.get(self._led, "green"),
            "mirror": self._mirror,
        }
