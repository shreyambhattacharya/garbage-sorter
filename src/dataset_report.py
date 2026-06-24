import sys
from pathlib import Path

from config import CLASS_NAMES, DATA_DIR, RAW_DIR, SPLITS, SUPPORTED_IMAGE_EXTENSIONS
from dataset_utils import create_required_folders, iter_image_files


def count_images(folder: Path) -> int:
    return sum(1 for _ in iter_image_files(folder))


def get_dataset_locations() -> dict[str, Path]:
    locations = {"raw": RAW_DIR}
    for split_name in SPLITS:
        locations[split_name] = DATA_DIR / split_name
    return locations


def print_report(counts: dict[str, dict[str, int]]) -> bool:
    has_zero_class = False

    print("\nDataset image report")
    print("-" * 58)
    print(f"{'split':<12}{'landfill':>11}{'compost':>11}{'recycling':>12}{'total':>10}")
    print("-" * 58)

    for split_name, class_counts in counts.items():
        split_total = sum(class_counts.values())
        print(
            f"{split_name:<12}"
            f"{class_counts['landfill']:>11}"
            f"{class_counts['compost']:>11}"
            f"{class_counts['recycling']:>12}"
            f"{split_total:>10}"
        )

    print("\nWarnings")
    print("-" * 58)
    for split_name, class_counts in counts.items():
        for class_name, image_count in class_counts.items():
            if image_count == 0:
                has_zero_class = True
                print(f"WARNING: data/{split_name}/{class_name} has zero images.")

    if not has_zero_class:
        print("No zero-image class folders found.")

    return has_zero_class


def main() -> int:
    create_required_folders()

    counts = {}
    for split_name, split_dir in get_dataset_locations().items():
        counts[split_name] = {}
        for class_name in CLASS_NAMES:
            counts[split_name][class_name] = count_images(split_dir / class_name)

    print_report(counts)
    print("\nSupported image types: " + ", ".join(sorted(SUPPORTED_IMAGE_EXTENSIONS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
