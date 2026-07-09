import argparse
import sys
from pathlib import Path

from config import (
    CAMERA_INDEX,
    CAMERA_MODE,
    CAPTURE_DIR,
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    MODEL_PATH,
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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Safe hardware and software diagnostics for garbage sorter bring-up."
    )
    parser.add_argument("--check-model", action="store_true", help="Verify the trained model can be loaded.")
    parser.add_argument("--image", help="Run inference on a saved image.")
    parser.add_argument("--check-camera", action="store_true", help="Capture one diagnostic camera frame.")
    parser.add_argument("--camera", choices=sorted(ALLOWED_CAMERA_MODES), default=CAMERA_MODE)
    parser.add_argument("--camera-index", type=int, default=CAMERA_INDEX)
    parser.add_argument("--check-sim", action="store_true", help="Run simulator ping/status/sort diagnostics.")
    parser.add_argument("--check-serial-ping", action="store_true", help="Send PING to STM32 and expect PONG.")
    parser.add_argument("--check-serial-sort", choices=CLASS_NAMES, help="Send a SORT command to STM32.")
    parser.add_argument("--test-diverters", action="store_true", help="Run STM32 TEST_DIVERTERS servo bring-up.")
    parser.add_argument("--test-trapdoor", action="store_true", help="Run STM32 TEST_TRAPDOOR servo bring-up.")
    parser.add_argument("--test-ultrasonic", action="store_true", help="Run STM32 TEST_ULTRASONIC.")
    parser.add_argument("--test-display", action="store_true", help="Run STM32 TEST_DISPLAY.")
    parser.add_argument("--port", default=SERIAL_PORT, help=f"Serial port, default {SERIAL_PORT}.")
    parser.add_argument("--full-sim", action="store_true", help="Run image inference plus simulated hardware sort.")
    return parser


def print_pass(name: str) -> bool:
    print(f"PASS: {name}")
    return True


def print_fail(name: str, message: str) -> bool:
    print(f"FAIL: {name}: {message}")
    return False


def check_model() -> bool:
    name = "model check"
    if not MODEL_PATH.exists():
        return print_fail(name, f"model file not found: {MODEL_PATH}")

    try:
        load_model()
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        return print_fail(name, str(exc))

    return print_pass(name)


def check_image_inference(image_path_text: str) -> bool:
    name = "image inference check"
    image_path = resolve_path(image_path_text)
    if not image_path.exists():
        return print_fail(name, f"image file not found: {image_path}")
    if not image_path.is_file():
        return print_fail(name, f"expected an image file but found a folder: {image_path}")

    try:
        result = predict_image_path(image_path)
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        return print_fail(name, str(exc))

    print_prediction_result(result)
    return print_pass(name)


def check_camera(camera_mode: str, camera_index: int) -> bool:
    name = "camera check"
    output_path = CAPTURE_DIR / "diagnostic_camera_test.jpg"
    camera = CameraCapture(mode=camera_mode, camera_index=camera_index)

    try:
        if not camera.start():
            return print_fail(name, f"could not start {camera_mode} camera")

        frame = camera.capture_frame()
        if frame is None:
            return print_fail(name, "camera did not return a frame")

        if not camera.save_frame(frame, output_path):
            return print_fail(name, f"could not save frame to {output_path}")
    except Exception as exc:
        return print_fail(name, str(exc))
    finally:
        camera.stop()

    print(f"Saved diagnostic camera image to {output_path}")
    return print_pass(name)


def check_simulator() -> bool:
    name = "simulator check"
    simulator = HardwareSimulator()

    try:
        print(f"Initial simulator status: {simulator.get_status()}")
        if not simulator.connect():
            return print_fail(name, "simulator connect failed")
        if not simulator.ping():
            return print_fail(name, "simulator ping failed")
        print(f"Connected simulator status: {simulator.get_status()}")
        if not simulator.send_sort_command("recycling", 0.90):
            return print_fail(name, "simulator sort failed")
        print(f"Final simulator status: {simulator.get_status()}")
        simulator.disconnect()
    except Exception as exc:
        return print_fail(name, str(exc))

    return print_pass(name)


def make_serial_hardware(port: str):
    from serial_hardware import SerialHardwareInterface

    return SerialHardwareInterface(
        port=port,
        baudrate=SERIAL_BAUDRATE,
        timeout_seconds=SERIAL_TIMEOUT_SECONDS,
        sort_timeout_seconds=SORT_COMMAND_TIMEOUT_SECONDS,
    )


def check_serial_ping(port: str) -> bool:
    name = "serial ping check"
    hardware = make_serial_hardware(port)

    try:
        if not hardware.ping():
            return print_fail(name, f"PING failed on {port}")
    finally:
        hardware.disconnect()

    return print_pass(name)


def check_serial_sort(class_name: str, port: str) -> bool:
    name = "serial sort check"
    print("WARNING: This sends a SORT command and may move connected servos.")
    print("Verify servo pulse ranges and mechanism clearance before running this test.")
    hardware = make_serial_hardware(port)

    try:
        if not hardware.send_sort_command(class_name, 0.90):
            return print_fail(name, f"SORT failed on {port}")
    finally:
        hardware.disconnect()

    return print_pass(name)


def check_serial_test(test_name: str, port: str) -> bool:
    name = f"{test_name.lower()} check"
    if test_name in {"TEST_DIVERTERS", "TEST_TRAPDOOR"}:
        print(f"WARNING: {test_name} may move connected servos.")
        print("Run no-load first and verify pulse ranges before attaching the mechanism.")

    hardware = make_serial_hardware(port)

    try:
        if not hardware.run_test_command(test_name):
            return print_fail(name, f"{test_name} failed on {port}")
    finally:
        hardware.disconnect()

    return print_pass(name)


def check_full_sim(image_path_text: str | None) -> bool:
    name = "full simulation check"
    if not image_path_text:
        return print_fail(name, "--full-sim requires --image path/to/image.jpg")

    image_path = resolve_path(image_path_text)
    if not image_path.exists():
        return print_fail(name, f"image file not found: {image_path}")
    if not image_path.is_file():
        return print_fail(name, f"expected an image file but found a folder: {image_path}")

    try:
        result = predict_image_path(image_path)
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        return print_fail(name, str(exc))

    print_prediction_result(result)
    decision = "ACCEPT" if result["confidence"] >= CONFIDENCE_THRESHOLD else "UNCERTAIN"
    result["decision"] = decision

    if decision == "UNCERTAIN":
        print("UNCERTAIN: confidence below threshold. Hardware command was not sent.")
        log_prediction(
            result["image_path"],
            result["predicted_class"],
            result["confidence"],
            decision,
            all_class_probabilities=result["probabilities"],
            hardware_mode="sim",
            hardware_success=None,
            error_message="confidence below threshold",
        )
        return print_pass(name)

    command_id = 1
    command = make_sort_command(result["predicted_class"], result["confidence"], command_id).strip()
    simulator = HardwareSimulator()
    try:
        hardware_success = simulator.send_sort_command(result["predicted_class"], result["confidence"])
    except Exception as exc:
        log_hardware_event(
            command_id,
            command,
            result["predicted_class"],
            result["confidence"],
            "sim",
            "ERROR",
            str(exc),
        )
        return print_fail(name, str(exc))

    log_prediction(
        result["image_path"],
        result["predicted_class"],
        result["confidence"],
        decision,
        all_class_probabilities=result["probabilities"],
        hardware_mode="sim",
        hardware_success=hardware_success,
        error_message="" if hardware_success else "simulated hardware command failed",
    )
    log_hardware_event(
        command_id,
        command,
        result["predicted_class"],
        result["confidence"],
        "sim",
        "SUCCESS" if hardware_success else "FAILED",
        "diagnostic simulated sort completed" if hardware_success else "diagnostic simulated sort failed",
    )

    if not hardware_success:
        return print_fail(name, "simulated hardware command failed")

    return print_pass(name)


def main() -> int:
    parser = parse_args()
    args = parser.parse_args()

    requested_checks = [
        args.check_model,
        bool(args.image and not args.full_sim),
        args.check_camera,
        args.check_sim,
        args.check_serial_ping,
        bool(args.check_serial_sort),
        args.test_diverters,
        args.test_trapdoor,
        args.test_ultrasonic,
        args.test_display,
        args.full_sim,
    ]

    if not any(requested_checks):
        parser.print_help()
        return 0

    results = []

    if args.check_model:
        results.append(check_model())
    if args.image and not args.full_sim:
        results.append(check_image_inference(args.image))
    if args.check_camera:
        results.append(check_camera(args.camera, args.camera_index))
    if args.check_sim:
        results.append(check_simulator())
    if args.check_serial_ping:
        results.append(check_serial_ping(args.port))
    if args.check_serial_sort:
        results.append(check_serial_sort(args.check_serial_sort, args.port))
    if args.test_diverters:
        results.append(check_serial_test("TEST_DIVERTERS", args.port))
    if args.test_trapdoor:
        results.append(check_serial_test("TEST_TRAPDOOR", args.port))
    if args.test_ultrasonic:
        results.append(check_serial_test("TEST_ULTRASONIC", args.port))
    if args.test_display:
        results.append(check_serial_test("TEST_DISPLAY", args.port))
    if args.full_sim:
        results.append(check_full_sim(args.image))

    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
