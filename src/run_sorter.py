import argparse
import sys
from datetime import datetime
from pathlib import Path

from config import (
    CAMERA_INDEX,
    CAMERA_MODE,
    CAPTURE_DIR,
    CONFIDENCE_THRESHOLD,
    HARDWARE_MODE,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
    SERIAL_TIMEOUT_SECONDS,
    SORT_COMMAND_TIMEOUT_SECONDS,
)
from dataset_utils import log_hardware_event, log_prediction
from hardware_simulator import HardwareSimulator
from pi_camera_capture import ALLOWED_CAMERA_MODES, CameraCapture
from predict_image import PredictionError, load_model, predict_image_path, print_prediction_result, resolve_path
from serial_protocol import make_sort_command
from system_state_machine import SorterStateMachine


def parse_args():
    parser = argparse.ArgumentParser(description="Main simulation-first garbage sorter runner.")
    parser.add_argument("--hardware", choices=["sim", "serial"], default=HARDWARE_MODE)
    parser.add_argument("--camera", choices=sorted(ALLOWED_CAMERA_MODES), default=CAMERA_MODE)
    parser.add_argument("--camera-index", type=int, default=CAMERA_INDEX)
    parser.add_argument("--image", help="Optional image path. If provided, camera capture is skipped.")
    parser.add_argument("--serial-port", default=SERIAL_PORT)
    return parser.parse_args()


def get_hardware_interface(hardware_mode: str, serial_port: str):
    if hardware_mode == "sim":
        return HardwareSimulator()

    from serial_hardware import SerialHardwareInterface

    return SerialHardwareInterface(
        port=serial_port,
        baudrate=SERIAL_BAUDRATE,
        timeout_seconds=SERIAL_TIMEOUT_SECONDS,
        sort_timeout_seconds=SORT_COMMAND_TIMEOUT_SECONDS,
    )


def next_capture_path() -> Path:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = CAPTURE_DIR / f"capture_{timestamp}.jpg"
    counter = 1
    while candidate.exists():
        candidate = CAPTURE_DIR / f"capture_{timestamp}_{counter}.jpg"
        counter += 1
    return candidate


def capture_image(camera_mode: str, camera_index: int, state_machine: SorterStateMachine) -> Path | None:
    state_machine.set_state("CAPTURING")
    camera = CameraCapture(mode=camera_mode, camera_index=camera_index)

    try:
        if not camera.start():
            state_machine.set_error("Camera could not be started.")
            return None

        input("Press ENTER to scan the item...")
        frame = camera.capture_frame()
        if frame is None:
            state_machine.set_error("Camera did not return a frame.")
            return None

        output_path = next_capture_path()
        if not camera.save_frame(frame, output_path):
            state_machine.set_error(f"Could not save captured image to {output_path}.")
            return None

        print(f"Saved captured image to {output_path}")
        return output_path
    finally:
        camera.stop()


def print_probabilities(probabilities: dict) -> None:
    print("\nClass probabilities:")
    for class_name, probability in probabilities.items():
        print(f"{class_name}: {probability:.2f}")


def log_no_hardware_prediction(result: dict, hardware_mode: str, error_message: str = "") -> None:
    log_prediction(
        result.get("image_path", ""),
        result["predicted_class"],
        result["confidence"],
        result["decision"],
        all_class_probabilities=result["probabilities"],
        hardware_mode=hardware_mode,
        hardware_success=None,
        error_message=error_message,
    )


def send_hardware_command(
    hardware,
    hardware_mode: str,
    predicted_class: str,
    confidence: float,
    command_id: int,
) -> tuple[bool, str]:
    command = make_sort_command(predicted_class, confidence, command_id).strip()
    try:
        success = hardware.send_sort_command(predicted_class, confidence)
    except Exception as exc:
        message = str(exc)
        log_hardware_event(command_id, command, predicted_class, confidence, hardware_mode, "ERROR", message)
        return False, message

    result = "SUCCESS" if success else "FAILED"
    message = "sort command completed" if success else "sort command failed"
    log_hardware_event(command_id, command, predicted_class, confidence, hardware_mode, result, message)
    return success, message


def main() -> int:
    args = parse_args()
    state_machine = SorterStateMachine()
    image_path = None

    if args.image:
        image_path = resolve_path(args.image)
        if not image_path.exists():
            state_machine.set_error(f"Image file not found: {image_path}")
            print(f"Image file not found: {image_path}")
            return 1
        if not image_path.is_file():
            state_machine.set_error(f"Expected an image file but found a folder: {image_path}")
            print(f"Expected an image file but found a folder: {image_path}")
            return 1

    try:
        model_bundle = load_model()
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        state_machine.set_error(str(exc))
        print(f"Sorter error:\n{exc}")
        return 1

    if not args.image:
        image_path = capture_image(args.camera, args.camera_index, state_machine)
        if image_path is None:
            print(f"Sorter error: {state_machine.last_error}")
            return 1

    state_machine.set_state("CLASSIFYING")
    try:
        result = predict_image_path(image_path, model_bundle=model_bundle)
    except (FileNotFoundError, PredictionError) as exc:
        state_machine.set_error(str(exc))
        print(f"Prediction error:\n{exc}")
        return 1

    state_machine.last_prediction = result["predicted_class"]
    state_machine.last_confidence = result["confidence"]

    print_prediction_result(result)
    result["decision"] = "ACCEPT" if result["confidence"] >= CONFIDENCE_THRESHOLD else "UNCERTAIN"

    if result["decision"] == "UNCERTAIN":
        state_machine.set_state("UNCERTAIN")
        print("Uncertain. Please reposition item or sort manually.")
        log_no_hardware_prediction(result, args.hardware)
        return 0

    state_machine.set_state("ACCEPTED")
    hardware = get_hardware_interface(args.hardware, args.serial_port)
    command_id = 1
    state_machine.last_command_id = command_id

    state_machine.set_state("SENDING_COMMAND")
    hardware_success, hardware_message = send_hardware_command(
        hardware,
        args.hardware,
        result["predicted_class"],
        result["confidence"],
        command_id,
    )
    hardware.disconnect()

    log_prediction(
        result["image_path"],
        result["predicted_class"],
        result["confidence"],
        result["decision"],
        all_class_probabilities=result["probabilities"],
        hardware_mode=args.hardware,
        hardware_success=hardware_success,
        error_message="" if hardware_success else hardware_message,
    )

    if not hardware_success:
        state_machine.set_error(hardware_message)
        print(f"Hardware command failed: {hardware_message}")
        return 1

    state_machine.set_state("SORTING")
    state_machine.set_state("COMPLETE")
    print("Sorter run complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
