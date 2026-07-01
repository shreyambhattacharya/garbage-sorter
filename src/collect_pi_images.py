import argparse
import sys
from pathlib import Path

from config import CAMERA_INDEX, CAMERA_MODE, CLASS_NAMES, RAW_DIR
from pi_camera_capture import ALLOWED_CAMERA_MODES, CameraCapture


def parse_args():
    parser = argparse.ArgumentParser(description="Collect real camera images into data/raw.")
    parser.add_argument(
        "--class",
        required=True,
        dest="class_name",
        choices=CLASS_NAMES,
        help="Final garbage class to collect.",
    )
    parser.add_argument(
        "--camera",
        choices=sorted(ALLOWED_CAMERA_MODES),
        default=CAMERA_MODE,
        help=f"Camera backend to use, default {CAMERA_MODE}.",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=CAMERA_INDEX,
        help=f"OpenCV camera index, default {CAMERA_INDEX}.",
    )
    return parser.parse_args()


def next_image_path(class_name: str) -> Path:
    class_dir = RAW_DIR / class_name
    class_dir.mkdir(parents=True, exist_ok=True)

    index = 1
    while True:
        candidate = class_dir / f"{class_name}_pi_{index:06d}.jpg"
        if not candidate.exists():
            return candidate
        index += 1


def collect_with_opencv(camera: CameraCapture, class_name: str) -> int:
    cv2 = camera.cv2
    collected_count = 0

    print("OpenCV collection mode")
    print("Press SPACE to capture an image. Press q to quit.")

    while True:
        frame = camera.capture_frame()
        if frame is None:
            break

        preview = frame.copy()
        cv2.putText(
            preview,
            f"Class: {class_name} | SPACE capture | q quit",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.imshow("Garbage Sorter Image Collection", preview)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == 32:
            output_path = next_image_path(class_name)
            if camera.save_frame(frame, output_path):
                collected_count += 1
                print(f"Captured {output_path}")

    cv2.destroyAllWindows()
    return collected_count


def collect_with_picamera2(camera: CameraCapture, class_name: str) -> int:
    collected_count = 0

    print("Picamera2 collection mode")
    print("Press Enter to capture an image. Type q and press Enter to quit.")

    while True:
        user_input = input("Capture image? ").strip().lower()
        if user_input == "q":
            break

        frame = camera.capture_frame()
        if frame is None:
            break

        output_path = next_image_path(class_name)
        if camera.save_frame(frame, output_path):
            collected_count += 1
            print(f"Captured {output_path}")

    return collected_count


def main() -> int:
    args = parse_args()
    class_name = args.class_name

    camera = CameraCapture(mode=args.camera, camera_index=args.camera_index)
    try:
        if not camera.start():
            return 1

        if args.camera == "opencv":
            collected_count = collect_with_opencv(camera, class_name)
        else:
            collected_count = collect_with_picamera2(camera, class_name)
    finally:
        camera.stop()

    print(f"Collected {collected_count} image(s) for class '{class_name}'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
