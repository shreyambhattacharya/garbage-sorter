import argparse
import csv
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

from config import (
    CAMERA_INDEX,
    CAMERA_MODE,
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    RESULTS_DIR,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
    SERIAL_TIMEOUT_SECONDS,
    SORT_COMMAND_TIMEOUT_SECONDS,
)
from pi_camera_capture import ALLOWED_CAMERA_MODES, CameraCapture
from predict_image import PredictionError, load_model, predict_pil_image, resolve_path
from serial_hardware import SerialHardwareInterface


LATENCY_CSV_PATH = RESULTS_DIR / "latency_summary.csv"
LATENCY_MD_PATH = RESULTS_DIR / "latency_summary.md"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Measure classify-to-route latency through Python inference and STM32 serial DONE."
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--image", help="Saved image path. Camera capture is skipped.")
    input_group.add_argument("--camera", choices=sorted(ALLOWED_CAMERA_MODES), default=None)
    parser.add_argument("--camera-index", type=int, default=CAMERA_INDEX)
    parser.add_argument("--port", default=SERIAL_PORT)
    parser.add_argument("--class", dest="forced_class", choices=CLASS_NAMES, help="Override serial sort class.")
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--confidence", type=float, default=0.90, help="Confidence used when --class overrides ML output.")
    return parser.parse_args()


def load_image_for_trial(args, model_bundle, camera: CameraCapture | None):
    Image = model_bundle["Image"]
    start = time.perf_counter()

    if args.image:
        image_path = resolve_path(args.image)
        if not image_path.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        with Image.open(image_path) as image:
            loaded_image = image.convert("RGB").copy()
        source = str(image_path)
    else:
        frame = camera.capture_frame()
        if frame is None:
            raise RuntimeError("Camera did not return a frame.")
        loaded_image = Image.fromarray(frame[:, :, ::-1]).convert("RGB")
        source = f"camera:{args.camera or CAMERA_MODE}:{args.camera_index}"

    elapsed = time.perf_counter() - start
    return loaded_image, source, elapsed


def run_trial(args, model_bundle, hardware: SerialHardwareInterface, camera: CameraCapture | None, trial_index: int):
    total_start = time.perf_counter()
    image, source, capture_load_seconds = load_image_for_trial(args, model_bundle, camera)

    inference_start = time.perf_counter()
    prediction = predict_pil_image(image, model_bundle)
    inference_seconds = time.perf_counter() - inference_start

    class_name = args.forced_class or prediction["predicted_class"]
    confidence = args.confidence if args.forced_class else prediction["confidence"]
    decision = "ACCEPT" if confidence >= CONFIDENCE_THRESHOLD else "UNCERTAIN"

    serial_seconds = 0.0
    hardware_success = False
    error_message = ""

    if decision == "ACCEPT":
        serial_start = time.perf_counter()
        hardware_success = hardware.send_sort_command(class_name, confidence)
        serial_seconds = time.perf_counter() - serial_start
        if not hardware_success:
            error_message = "serial SORT failed or STM32 returned ERROR"
    else:
        error_message = "confidence below threshold"

    total_seconds = time.perf_counter() - total_start

    return {
        "trial": trial_index,
        "source": source,
        "predicted_class": prediction["predicted_class"],
        "sort_class": class_name,
        "confidence": confidence,
        "decision": decision,
        "capture_load_seconds": capture_load_seconds,
        "inference_seconds": inference_seconds,
        "serial_sort_seconds": serial_seconds,
        "total_seconds": total_seconds,
        "hardware_success": hardware_success,
        "error_message": error_message,
    }


def save_latency_outputs(rows: list[dict], args) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "trial",
        "source",
        "predicted_class",
        "sort_class",
        "confidence",
        "decision",
        "capture_load_seconds",
        "inference_seconds",
        "serial_sort_seconds",
        "total_seconds",
        "hardware_success",
        "error_message",
    ]

    with LATENCY_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    successful_totals = [row["total_seconds"] for row in rows if row["hardware_success"]]
    all_totals = [row["total_seconds"] for row in rows]
    summary_values = successful_totals or all_totals

    lines = [
        "# Latency Summary",
        "",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Trials requested: `{args.trials}`",
        f"- Trials recorded: `{len(rows)}`",
        f"- Serial port: `{args.port}`",
        f"- Input mode: `{'image' if args.image else 'camera'}`",
        "",
        "Latency includes image capture/load, preprocessing, MobileNetV3 inference, confidence thresholding, serial SORT command transmission, STM32 ACK/DONE response handling, diverter servo movement, and trapdoor open/close motion.",
        "",
    ]

    if summary_values:
        lines.extend(
            [
                "| Metric | Result |",
                "|---|---:|",
                f"| Average latency | {statistics.mean(summary_values):.3f} s |",
                f"| Minimum latency | {min(summary_values):.3f} s |",
                f"| Maximum latency | {max(summary_values):.3f} s |",
                f"| Trials | {len(summary_values)} |",
            ]
        )
    else:
        lines.append("No trials were recorded.")

    LATENCY_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.trials <= 0:
        print("--trials must be a positive integer.")
        return 1

    try:
        model_bundle = load_model()
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        print(f"Model error:\n{exc}")
        return 1

    camera = None
    if args.camera:
        camera = CameraCapture(mode=args.camera or CAMERA_MODE, camera_index=args.camera_index)
        if not camera.start():
            print(f"Could not start camera mode {args.camera}.")
            return 1

    hardware = SerialHardwareInterface(
        port=args.port,
        baudrate=SERIAL_BAUDRATE,
        timeout_seconds=SERIAL_TIMEOUT_SECONDS,
        sort_timeout_seconds=SORT_COMMAND_TIMEOUT_SECONDS,
    )

    rows = []
    try:
        if not hardware.connect():
            return 1

        for trial_index in range(1, args.trials + 1):
            print(f"Trial {trial_index}/{args.trials}")
            row = run_trial(args, model_bundle, hardware, camera, trial_index)
            rows.append(row)
            print(
                f"  class={row['sort_class']} decision={row['decision']} "
                f"total={row['total_seconds']:.3f}s success={row['hardware_success']}"
            )
    except Exception as exc:
        print(f"Latency measurement error: {exc}")
        return 1
    finally:
        hardware.disconnect()
        if camera is not None:
            camera.stop()

    save_latency_outputs(rows, args)
    print(f"Saved latency CSV to {LATENCY_CSV_PATH}")
    print(f"Saved latency summary to {LATENCY_MD_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
