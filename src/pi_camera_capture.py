from pathlib import Path

from config import CAMERA_INDEX, CAMERA_MODE


ALLOWED_CAMERA_MODES = {"opencv", "picamera2"}


class CameraCapture:
    """Small camera wrapper for OpenCV USB/laptop cameras and Raspberry Pi Picamera2."""

    def __init__(self, mode: str, camera_index: int = 0):
        if mode not in ALLOWED_CAMERA_MODES:
            raise ValueError(
                f"Invalid camera mode '{mode}'. Expected one of: {', '.join(sorted(ALLOWED_CAMERA_MODES))}"
            )

        self.mode = mode
        self.camera_index = camera_index
        self.camera = None
        self.cv2 = None

    def start(self) -> bool:
        if self.mode == "opencv":
            return self._start_opencv()
        return self._start_picamera2()

    def capture_frame(self):
        if self.mode == "opencv":
            return self._capture_opencv_frame()
        return self._capture_picamera2_frame()

    def save_frame(self, frame, output_path) -> bool:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cv2 = self._load_cv2()
        if cv2 is None:
            return False

        frame_to_save = frame
        if self.mode == "picamera2":
            frame_to_save = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        ok = cv2.imwrite(str(output_path), frame_to_save)
        if not ok:
            print(f"Camera error: could not save image to {output_path}")
            return False
        return True

    def stop(self) -> None:
        if self.camera is None:
            return

        if self.mode == "opencv":
            self.camera.release()
        else:
            self.camera.stop()

        self.camera = None

    def _load_cv2(self):
        if self.cv2 is not None:
            return self.cv2

        try:
            import cv2
        except Exception:
            print("Camera error: OpenCV is not installed. Run: pip install -r requirements.txt")
            return None

        self.cv2 = cv2
        return self.cv2

    def _start_opencv(self) -> bool:
        cv2 = self._load_cv2()
        if cv2 is None:
            return False

        self.camera = cv2.VideoCapture(self.camera_index)
        if not self.camera.isOpened():
            print(f"Camera error: OpenCV camera index {self.camera_index} is unavailable.")
            self.camera.release()
            self.camera = None
            return False

        return True

    def _capture_opencv_frame(self):
        if self.camera is None:
            print("Camera error: OpenCV camera has not been started.")
            return None

        ok, frame = self.camera.read()
        if not ok:
            print("Camera error: could not read a frame from the OpenCV camera.")
            return None

        return frame

    def _start_picamera2(self) -> bool:
        try:
            from picamera2 import Picamera2
        except Exception:
            print("Camera error: Picamera2 is not installed. Use --camera opencv on Windows/laptop.")
            return False

        self.camera = Picamera2()
        self.camera.configure(self.camera.create_still_configuration())
        self.camera.start()
        return True

    def _capture_picamera2_frame(self):
        if self.camera is None:
            print("Camera error: Picamera2 camera has not been started.")
            return None

        return self.camera.capture_array()


def capture_single_image(output_path: Path, mode: str = CAMERA_MODE):
    camera = CameraCapture(mode=mode, camera_index=CAMERA_INDEX)
    try:
        if not camera.start():
            return False

        frame = camera.capture_frame()
        if frame is None:
            return False

        return camera.save_frame(frame, output_path)
    finally:
        camera.stop()
