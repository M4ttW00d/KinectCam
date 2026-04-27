import subprocess
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VirtualCamera:
    def __init__(self, device: str = "/dev/video10", width: int = 640, height: int = 480, fps: int = 30):
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self._proc = None

    def open(self):
        cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-f", "rawvideo",
            "-pixel_format", "rgb24",
            "-video_size", f"{self.width}x{self.height}",
            "-framerate", str(self.fps),
            "-i", "pipe:0",
            "-f", "v4l2",
            "-pix_fmt", "yuyv422",
            self.device,
        ]
        try:
            self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
            logger.info(f"Virtual camera opened via ffmpeg on {self.device}")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found — install with: sudo apt install ffmpeg") from None
        except Exception as e:
            raise RuntimeError(f"Could not open virtual camera on {self.device}: {e}") from e

    def write_frame(self, frame_rgb: np.ndarray):
        if self._proc is None or self._proc.poll() is not None:
            return
        try:
            self._proc.stdin.write(frame_rgb.tobytes())
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            logger.debug(f"Frame write error: {e}")

    def close(self):
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=2)
            except Exception:
                self._proc.kill()
            self._proc = None
