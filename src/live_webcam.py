import sys

from config import (
    BACKGROUND_CALIBRATION_FRAMES,
    BACKGROUND_LEARNING_RATE,
    FOREGROUND_THRESHOLD,
    MODEL_PATH,
    OBJECT_CLEAR_FRAMES,
    OBJECT_PRESENT_AREA_RATIO,
    OBJECT_STABLE_FRAMES,
    WEBCAM_ROI_HEIGHT_RATIO,
    WEBCAM_ROI_WIDTH_RATIO,
)
from dataset_utils import log_prediction
from hardware_simulator import send_sort_command
from predict_image import PredictionError, load_model, predict_pil_image


def load_cv2():
    try:
        import cv2
    except Exception as exc:
        raise RuntimeError(
            "Could not import OpenCV. Install requirements with:\n"
            "pip install -r requirements.txt"
        ) from exc

    return cv2


def draw_result(cv2, frame, result):
    label = f"{result['predicted_class']} {result['confidence']:.2f} {result['decision']}"
    color = (0, 180, 0) if result["decision"] == "ACCEPT" else (0, 165, 255)
    cv2.rectangle(frame, (10, 10), (620, 70), (0, 0, 0), -1)
    cv2.putText(frame, label, (25, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)


def get_marked_spot(frame):
    height, width = frame.shape[:2]
    roi_width = int(width * WEBCAM_ROI_WIDTH_RATIO)
    roi_height = int(height * WEBCAM_ROI_HEIGHT_RATIO)
    x1 = (width - roi_width) // 2
    y1 = (height - roi_height) // 2
    x2 = x1 + roi_width
    y2 = y1 + roi_height
    return x1, y1, x2, y2


def get_roi(frame, roi_box):
    x1, y1, x2, y2 = roi_box
    return frame[y1:y2, x1:x2]


def preprocess_roi(cv2, roi_frame):
    gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)


def foreground_fraction(cv2, current_roi_gray, background_roi):
    background_uint8 = cv2.convertScaleAbs(background_roi)
    difference = cv2.absdiff(background_uint8, current_roi_gray)
    _, mask = cv2.threshold(difference, FOREGROUND_THRESHOLD, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, None, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_DILATE, None, iterations=2)
    return cv2.countNonZero(mask) / mask.size


def draw_marked_spot(cv2, frame, roi_box, status, object_fraction):
    x1, y1, x2, y2 = roi_box
    color = (0, 200, 0)
    if status.startswith("DETECTED"):
        color = (0, 165, 255)
    elif status.startswith("SORTED") or status.startswith("UNCERTAIN"):
        color = (255, 180, 0)
    elif status.startswith("CALIBRATING"):
        color = (255, 255, 0)

    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
    cv2.rectangle(frame, (10, frame.shape[0] - 80), (720, frame.shape[0] - 15), (0, 0, 0), -1)
    cv2.putText(
        frame,
        f"{status} | object area {object_fraction:.2f}",
        (25, frame.shape[0] - 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
    )


def print_probabilities(result):
    print("\nClass probabilities:")
    for class_name, probability in result["probabilities"].items():
        print(f"{class_name}: {probability:.2f}")
    print(f"Decision: {result['decision']}")


def classify_roi(cv2, roi_frame, model_bundle):
    rgb_frame = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2RGB)
    pil_image = model_bundle["Image"].fromarray(rgb_frame)
    return predict_pil_image(pil_image, model_bundle)


def handle_prediction(result):
    print(f"\nPrediction: {result['predicted_class']} ({result['confidence']:.2f})")
    print_probabilities(result)

    log_prediction(
        "webcam_auto_capture",
        result["predicted_class"],
        result["confidence"],
        result["decision"],
    )

    if result["decision"] == "ACCEPT":
        send_sort_command(result["predicted_class"], result["confidence"])
    else:
        print("Please reposition item or sort manually.")


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"Model file not found: {MODEL_PATH}")
        print("Train a model first with: python src/train.py")
        return 1

    try:
        model_bundle = load_model()
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        print(f"Could not load model:\n{exc}")
        return 1

    try:
        cv2 = load_cv2()
    except RuntimeError as exc:
        print(exc)
        return 1

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Webcam unavailable. Check that your laptop camera is connected and not in use.")
        return 1

    print("Automatic webcam demo running.")
    print("Keep the marked spot empty during startup calibration.")
    print("After calibration, place one item on the marked spot. Press Q to quit.")

    last_result = None
    background_roi = None
    calibration_frames = 0
    stable_object_frames = 0
    clear_frames = 0
    waiting_for_removal = False
    status = "CALIBRATING"
    object_fraction = 0.0

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Could not read from webcam.")
                return 1

            display_frame = frame.copy()
            roi_box = get_marked_spot(frame)
            roi_frame = get_roi(frame, roi_box)
            roi_gray = preprocess_roi(cv2, roi_frame)

            if background_roi is None:
                background_roi = roi_gray.astype("float")

            if calibration_frames < BACKGROUND_CALIBRATION_FRAMES:
                cv2.accumulateWeighted(roi_gray, background_roi, 0.1)
                calibration_frames += 1
                status = f"CALIBRATING {calibration_frames}/{BACKGROUND_CALIBRATION_FRAMES}"
                object_fraction = 0.0
            else:
                object_fraction = foreground_fraction(cv2, roi_gray, background_roi)
                object_present = object_fraction >= OBJECT_PRESENT_AREA_RATIO

                if waiting_for_removal:
                    if object_present:
                        clear_frames = 0
                        status = "SORTED - REMOVE ITEM"
                    else:
                        clear_frames += 1
                        cv2.accumulateWeighted(
                            roi_gray,
                            background_roi,
                            BACKGROUND_LEARNING_RATE,
                        )
                        status = f"RESETTING {clear_frames}/{OBJECT_CLEAR_FRAMES}"
                        if clear_frames >= OBJECT_CLEAR_FRAMES:
                            waiting_for_removal = False
                            clear_frames = 0
                            stable_object_frames = 0
                            status = "READY - PLACE ITEM"
                else:
                    if object_present:
                        stable_object_frames += 1
                        status = f"DETECTED {stable_object_frames}/{OBJECT_STABLE_FRAMES}"

                        if stable_object_frames >= OBJECT_STABLE_FRAMES:
                            last_result = classify_roi(cv2, roi_frame, model_bundle)
                            handle_prediction(last_result)
                            waiting_for_removal = True
                            clear_frames = 0
                            stable_object_frames = 0
                            status = (
                                "SORTED - REMOVE ITEM"
                                if last_result["decision"] == "ACCEPT"
                                else "UNCERTAIN - REMOVE ITEM"
                            )
                    else:
                        stable_object_frames = 0
                        status = "READY - PLACE ITEM"
                        cv2.accumulateWeighted(
                            roi_gray,
                            background_roi,
                            BACKGROUND_LEARNING_RATE,
                        )

            draw_marked_spot(cv2, display_frame, roi_box, status, object_fraction)
            if last_result is not None:
                draw_result(cv2, display_frame, last_result)

            cv2.imshow("Garbage Sorter Webcam Demo", display_frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
