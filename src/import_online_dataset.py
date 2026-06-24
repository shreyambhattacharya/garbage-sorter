import argparse
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

from config import CLASS_NAMES, RAW_DIR, SUPPORTED_IMAGE_EXTENSIONS
from dataset_utils import create_required_folders, iter_image_files


SOURCE_CLASS_TO_TARGET = {
    "cardboard": "recycling",
    "paper": "recycling",
    "glass": "recycling",
    "metal": "recycling",
    "plastic": "recycling",
    "recyclable": "recycling",
    "recycling": "recycling",
    "biological": "compost",
    "organic": "compost",
    "compost": "compost",
    "food": "compost",
    "food_waste": "compost",
    "vegetable": "compost",
    "fruit": "compost",
    "trash": "landfill",
    "garbage": "landfill",
    "landfill": "landfill",
    "non_recyclable": "landfill",
    "nonrecyclable": "landfill",
    "wrappers": "landfill",
    "wrapper": "landfill",
    "foam": "landfill",
    "styrofoam": "landfill",
}

IGNORED_CLASSES = {
    "hazardous",
    "battery",
    "batteries",
    "electronics",
    "e_waste",
    "clothes",
    "shoes",
    "medical",
    "unknown",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Import a local online-style waste dataset into data/raw."
    )
    parser.add_argument(
        "source_dataset",
        help="Local folder containing an online waste dataset with class subfolders.",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=None,
        help="Maximum number of images to copy into each final raw class.",
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Remove existing image files from data/raw/landfill, compost, and recycling first.",
    )
    args = parser.parse_args()

    if args.max_per_class is not None and args.max_per_class < 1:
        parser.error("--max-per-class must be greater than 0.")

    return args


def normalize_class_name(class_name: str) -> str:
    normalized = class_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def clear_existing_raw_images() -> int:
    removed_count = 0

    for class_name in CLASS_NAMES:
        raw_class_dir = RAW_DIR / class_name
        raw_class_dir.mkdir(parents=True, exist_ok=True)

        for image_path in iter_image_files(raw_class_dir):
            image_path.unlink()
            removed_count += 1

    return removed_count


def resolve_source_dataset(path_text: str) -> Path:
    source_path = Path(path_text).expanduser()
    if not source_path.exists():
        raise FileNotFoundError(f"Source dataset folder not found: {source_path}")
    if not source_path.is_dir():
        raise NotADirectoryError(f"Expected a folder, but found a file: {source_path}")
    return source_path


def map_source_class(source_class_name: str) -> str | None:
    normalized_name = normalize_class_name(source_class_name)
    if normalized_name in IGNORED_CLASSES:
        return None
    return SOURCE_CLASS_TO_TARGET.get(normalized_name)


def next_destination_path(
    destination_dir: Path,
    source_class_name: str,
    suffix: str,
    counters: dict[tuple[str, str], int],
) -> Path:
    source_prefix = normalize_class_name(source_class_name) or "unknown"
    key = (str(destination_dir), source_prefix)
    suffix = suffix.lower()

    while True:
        counters[key] += 1
        candidate = destination_dir / f"{source_prefix}_{counters[key]:06d}{suffix}"
        if not candidate.exists():
            return candidate


def import_images(
    source_dataset: Path,
    max_per_class: int | None,
) -> tuple[Counter, int, set[str], int]:
    copied_counts = Counter({class_name: 0 for class_name in CLASS_NAMES})
    copied_this_run = Counter({class_name: 0 for class_name in CLASS_NAMES})
    ignored_count = 0
    ignored_class_names = set()
    destination_counters = defaultdict(int)

    image_paths = sorted(iter_image_files(source_dataset))

    for image_path in image_paths:
        source_class_name = image_path.parent.name
        mapped_class = map_source_class(source_class_name)

        if mapped_class is None:
            ignored_count += 1
            ignored_class_names.add(source_class_name)
            continue

        if max_per_class is not None and copied_this_run[mapped_class] >= max_per_class:
            ignored_count += 1
            ignored_class_names.add(source_class_name)
            continue

        destination_dir = RAW_DIR / mapped_class
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = next_destination_path(
            destination_dir,
            source_class_name,
            image_path.suffix,
            destination_counters,
        )
        shutil.copy2(image_path, destination_path)
        copied_counts[mapped_class] += 1
        copied_this_run[mapped_class] += 1

    return copied_counts, ignored_count, ignored_class_names, len(image_paths)


def print_summary(
    copied_counts: Counter,
    ignored_count: int,
    ignored_class_names: set[str],
    scanned_image_count: int,
) -> None:
    print("\nOnline dataset import summary")
    print("-" * 38)
    print(f"Images scanned: {scanned_image_count}")
    print(f"Copied to landfill: {copied_counts['landfill']}")
    print(f"Copied to compost: {copied_counts['compost']}")
    print(f"Copied to recycling: {copied_counts['recycling']}")
    print(f"Ignored: {ignored_count}")

    if ignored_class_names:
        print("Ignored class names:")
        for class_name in sorted(ignored_class_names):
            print(f"- {class_name}")
    else:
        print("Ignored class names: none")


def main() -> int:
    args = parse_args()
    create_required_folders()

    try:
        source_dataset = resolve_source_dataset(args.source_dataset)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"Import error:\n{exc}")
        return 1

    if args.clear_existing:
        removed_count = clear_existing_raw_images()
        print(f"Cleared {removed_count} existing image files from data/raw.")

    copied_counts, ignored_count, ignored_class_names, scanned_image_count = import_images(
        source_dataset,
        args.max_per_class,
    )
    print_summary(copied_counts, ignored_count, ignored_class_names, scanned_image_count)

    if scanned_image_count == 0:
        print(
            "\nNo supported image files found in the source dataset. "
            "Supported types: " + ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS))
        )
        return 1

    total_copied = sum(copied_counts.values())
    if total_copied == 0:
        print("\nNo images were copied because no source classes matched the mapping.")
        return 1

    print("\nOriginal dataset files were copied, not moved or deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
