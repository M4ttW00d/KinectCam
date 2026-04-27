import signal
import sys
import time
import threading
import logging

import uvicorn

from kinect import KinectManager
from virtual_camera import VirtualCamera
from config import load as load_settings
import server as app_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

VCAM_DEVICE = "/dev/video36"
WEB_HOST = "127.0.0.1"
WEB_PORT = 36000
TARGET_FPS = 30


def frame_pump(kinect: KinectManager, vcam: VirtualCamera):
    interval = 1 / TARGET_FPS
    while True:
        frame = kinect.get_frame()
        if frame is not None:
            vcam.write_frame(frame)
        time.sleep(interval)


def main():
    kinect = KinectManager()
    vcam = VirtualCamera(device=VCAM_DEVICE)

    app_server.kinect = kinect
    app_server.vcam = vcam

    try:
        vcam.open()
    except RuntimeError as e:
        logger.error(str(e))
        sys.exit(1)

    kinect.start()

    settings = load_settings()
    kinect.set_tilt(settings["tilt"])
    kinect.set_led(settings["led"])
    kinect.set_mirror(settings["mirror"])

    pump = threading.Thread(target=frame_pump, args=(kinect, vcam), daemon=True)
    pump.start()

    def shutdown(sig, frame):
        logger.info("Shutting down KinectCam...")
        kinect.stop()
        vcam.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    logger.info(f"KinectCam running — open http://localhost:{WEB_PORT} in your browser")

    config = uvicorn.Config(
        app_server.app,
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="warning",
    )
    uvicorn.Server(config).run()


if __name__ == "__main__":
    main()
