import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Sequence

from config import (
    CLASS_NAMES,
    DATA_DIR,
    HARDWARE_LOG_PATH,
    LOGS_DIR,
    MODELS_DIR,
    PREDICTIONS_LOG_PATH,
    RAW_DIR,
    SPLITS,
    SUPPORTED_IMAGE_EXTENSIONS,
)


class DatasetError(RuntimeError):
    """Raised when the dataset folder structure is missing or invalid."""


def create_required_folders() -> None:
    """Create the expected data, model, and log folders if needed."""
    for class_name in CLASS_NAMES:
        (RAW_DIR / class_name).mkdir(parents=True, exist_ok=True)

    for split in SPLITS:
        for class_name in CLASS_NAMES:
            (DATA_DIR / split / class_name).mkdir(parents=True, exist_ok=True)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def validate_class_names(found_class_names: Sequence[str]) -> None:
    """Check that a list of class names matches the project classes."""
    found = set(found_class_names)
    expected = set(CLASS_NAMES)

    missing = sorted(expected - found)
    unexpected = sorted(found - expected)

    if missing or unexpected:
        parts = []
        if missing:
            parts.append(f"missing classes: {', '.join(missing)}")
        if unexpected:
            parts.append(f"unexpected classes: {', '.join(unexpected)}")
        raise DatasetError("Invalid class folders; " + "; ".join(parts))


def check_split_folder(split_name: str) -> Path:
    """Return a split folder path after verifying that it exists."""
    if split_name not in SPLITS:
        raise DatasetError(
            f"Unknown split '{split_name}'. Expected one of: {', '.join(SPLITS)}"
        )

    split_dir = DATA_DIR / split_name
    if not split_dir.exists():
        raise DatasetError(
            f"Missing dataset split folder: {split_dir}\n"
            "Run this project once to create folders, then add images."
        )
    if not split_dir.is_dir():
        raise DatasetError(f"Expected a folder but found a file: {split_dir}")

    return split_dir


def check_class_folders(split_name: str) -> Dict[str, Path]:
    """Check that every required class folder exists for a split."""
    split_dir = check_split_folder(split_name)

    class_dirs = {}
    for class_name in CLASS_NAMES:
        class_dir = split_dir / class_name
        if not class_dir.exists():
            raise DatasetError(
                f"Missing class folder: {class_dir}\n"
                f"Expected folders: {', '.join(CLASS_NAMES)}"
            )
        if not class_dir.is_dir():
            raise DatasetError(f"Expected a folder but found a file: {class_dir}")
        class_dirs[class_name] = class_dir

    actual_class_folders = [
        path.name for path in split_dir.iterdir() if path.is_dir() and not path.name.startswith(".")
    ]
    validate_class_names(actual_class_folders)

    return class_dirs


def iter_image_files(folder: Path) -> Iterable[Path]:
    """Yield supported image files below a folder."""
    for path in folder.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            yield path


def count_images_by_class(split_name: str) -> Dict[str, int]:
    """Count supported image files for each class in a split."""
    class_dirs = check_class_folders(split_name)
    return {
        class_name: sum(1 for _ in iter_image_files(class_dir))
        for class_name, class_dir in class_dirs.items()
    }


def split_contains_images(split_name: str) -> bool:
    """Return True if a split has at least one supported image file."""
    return sum(count_images_by_class(split_name).values()) > 0


def validate_dataset_split(
    split_name: str,
    require_images: bool = True,
    require_each_class: bool = False,
) -> Dict[str, int]:
    """Validate a split and return image counts by class."""
    counts = count_images_by_class(split_name)
    total_images = sum(counts.values())

    if require_images and total_images == 0:
        raise DatasetError(
            f"No images found in data/{split_name}.\n"
            f"Add images under: {DATA_DIR / split_name}\n"
            "Supported image types: .jpg, .jpeg, .png, .bmp, .webp"
        )

    if require_each_class:
        empty_classes = [class_name for class_name, count in counts.items() if count == 0]
        if empty_classes:
            raise DatasetError(
                f"The data/{split_name} split has empty class folders: "
                f"{', '.join(empty_classes)}\n"
                "Add at least one image to each class folder before continuing."
            )

    return counts


def log_prediction(
    image_path: str | Path,
    predicted_class: str,
    confidence: float,
    decision: str,
    all_class_probabilities: dict | None = None,
    hardware_mode: str = "",
    hardware_success: bool | None = None,
    error_message: str = "",
) -> None:
    """Append a prediction row to logs/predictions.csv."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "image_path",
        "predicted_class",
        "confidence",
        "decision",
        "all_class_probabilities",
        "hardware_mode",
        "hardware_success",
        "error_message",
    ]
    _ensure_csv_header(PREDICTIONS_LOG_PATH, fieldnames)

    with PREDICTIONS_LOG_PATH.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "image_path": str(image_path),
                "predicted_class": predicted_class,
                "confidence": f"{confidence:.4f}",
                "decision": decision,
                "all_class_probabilities": json.dumps(all_class_probabilities or {}),
                "hardware_mode": hardware_mode,
                "hardware_success": "" if hardware_success is None else str(hardware_success),
                "error_message": error_message,
            }
        )


def log_hardware_event(
    command_id: int,
    command: str,
    class_name: str,
    confidence: float,
    hardware_mode: str,
    result: str,
    message: str,
) -> None:
    """Append a hardware event row to logs/hardware_events.csv."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "timestamp",
        "command_id",
        "command",
        "class_name",
        "confidence",
        "hardware_mode",
        "result",
        "message",
    ]
    _ensure_csv_header(HARDWARE_LOG_PATH, fieldnames)

    with HARDWARE_LOG_PATH.open("a", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "command_id": command_id,
                "command": command,
                "class_name": class_name,
                "confidence": f"{confidence:.4f}",
                "hardware_mode": hardware_mode,
                "result": result,
                "message": message,
            }
        )


def _ensure_csv_header(csv_path: Path, fieldnames: list[str]) -> None:
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            csv.DictWriter(csv_file, fieldnames=fieldnames).writeheader()
        return

    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        existing_fieldnames = reader.fieldnames or []
        rows = list(reader)

    if existing_fieldnames == fieldnames:
        return

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({fieldname: row.get(fieldname, "") for fieldname in fieldnames})
