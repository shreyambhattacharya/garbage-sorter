import argparse
import random
import shutil
import sys
from pathlib import Path

from config import CLASS_NAMES, DATA_DIR, RAW_DIR, SPLITS, SUPPORTED_IMAGE_EXTENSIONS
from dataset_utils import create_required_folders, iter_image_files


DEFAULT_TRAIN_RATIO = 0.80
DEFAULT_VAL_RATIO = 0.10
DEFAULT_TEST_RATIO = 0.10
DEFAULT_SEED = 42


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy raw garbage images into train/val/test folders."
    )
    parser.add_argument("--train-ratio", type=float, default=DEFAULT_TRAIN_RATIO)
    parser.add_argument("--val-ratio", type=float, default=DEFAULT_VAL_RATIO)
    parser.add_argument("--test-ratio", type=float, default=DEFAULT_TEST_RATIO)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Remove existing image files from data/train, data/val, and data/test first.",
    )
    args = parser.parse_args()

    validate_ratios(parser, args.train_ratio, args.val_ratio, args.test_ratio)
    return args


def validate_ratios(parser, train_ratio: float, val_ratio: float, test_ratio: float) -> None:
    ratios = {
        "train-ratio": train_ratio,
        "val-ratio": val_ratio,
        "test-ratio": test_ratio,
    }

    for name, value in ratios.items():
        if value < 0:
            parser.error(f"--{name} must be greater than or equal to 0.")

    total = train_ratio + val_ratio + test_ratio
    if abs(total - 1.0) > 1e-6:
        parser.error(
            "--train-ratio, --val-ratio, and --test-ratio must add up to 1.0 "
            f"(got {total:.4f})."
        )


def clear_existing_split_images() -> int:
    removed_count = 0

    for split_name in SPLITS:
        for class_name in CLASS_NAMES:
            class_dir = DATA_DIR / split_name / class_name
            class_dir.mkdir(parents=True, exist_ok=True)

            for image_path in iter_image_files(class_dir):
                image_path.unlink()
                removed_count += 1

    return removed_count


def get_raw_images(class_name: str) -> list[Path]:
    raw_class_dir = RAW_DIR / class_name
    raw_class_dir.mkdir(parents=True, exist_ok=True)
    return sorted(iter_image_files(raw_class_dir))


def split_images(
    image_paths: list[Path],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> dict[str, list[Path]]:
    shuffled_images = list(image_paths)
    random.Random(seed).shuffle(shuffled_images)

    total = len(shuffled_images)
    train_count = int(total * train_ratio)
    val_count = int(total * val_ratio)

    train_images = shuffled_images[:train_count]
    val_images = shuffled_images[train_count : train_count + val_count]
    test_images = shuffled_images[train_count + val_count :]

    return {
        "train": train_images,
        "val": val_images,
        "test": test_images,
    }


def unique_destination_path(destination_dir: Path, source_path: Path) -> Path:
    candidate = destination_dir / source_path.name
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = destination_dir / f"{source_path.stem}_{counter}{source_path.suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def copy_split_images(class_name: str, split_map: dict[str, list[Path]]) -> dict[str, int]:
    copied_counts = {split_name: 0 for split_name in SPLITS}

    for split_name, image_paths in split_map.items():
        destination_dir = DATA_DIR / split_name / class_name
        destination_dir.mkdir(parents=True, exist_ok=True)

        for image_path in image_paths:
            destination_path = unique_destination_path(destination_dir, image_path)
            shutil.copy2(image_path, destination_path)
            copied_counts[split_name] += 1

    return copied_counts


def print_summary(summary: dict[str, dict[str, int]]) -> None:
    print("\nDataset split summary")
    print("-" * 58)
    print(f"{'class':<14}{'raw':>8}{'train':>9}{'val':>9}{'test':>9}{'total':>9}")
    print("-" * 58)

    for class_name in CLASS_NAMES:
        row = summary[class_name]
        copied_total = row["train"] + row["val"] + row["test"]
        print(
            f"{class_name:<14}"
            f"{row['raw']:>8}"
            f"{row['train']:>9}"
            f"{row['val']:>9}"
            f"{row['test']:>9}"
            f"{copied_total:>9}"
        )


def main() -> int:
    args = parse_args()
    create_required_folders()

    if args.clear_existing:
        removed_count = clear_existing_split_images()
        print(f"Cleared {removed_count} existing image files from data/train, data/val, and data/test.")

    summary = {}
    total_raw_images = 0

    for class_name in CLASS_NAMES:
        raw_images = get_raw_images(class_name)
        total_raw_images += len(raw_images)

        split_map = split_images(
            raw_images,
            args.train_ratio,
            args.val_ratio,
            args.seed,
        )
        copied_counts = copy_split_images(class_name, split_map)

        summary[class_name] = {
            "raw": len(raw_images),
            "train": copied_counts["train"],
            "val": copied_counts["val"],
            "test": copied_counts["test"],
        }

    print_summary(summary)

    if total_raw_images == 0:
        print(f"\nNo raw images found under: {RAW_DIR}")
        print("Add images to data/raw/landfill, data/raw/compost, and data/raw/recycling.")
        print("Supported image types: " + ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS)))
        return 1

    print("\nRaw images were copied, not moved or deleted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
