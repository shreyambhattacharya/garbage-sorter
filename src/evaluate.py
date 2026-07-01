import csv
import shutil
import sys
from pathlib import Path

from config import (
    BATCH_SIZE,
    CLASS_NAMES,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    LOGS_DIR,
    MODEL_PATH,
    SUPPORTED_IMAGE_EXTENSIONS,
    TEST_DIR,
)
from dataset_utils import DatasetError, create_required_folders, validate_dataset_split


MISCLASSIFIED_CSV_PATH = LOGS_DIR / "misclassified.csv"
MISCLASSIFIED_IMAGES_DIR = LOGS_DIR / "misclassified_images"


def load_evaluation_dependencies():
    try:
        import torch
        from sklearn.metrics import confusion_matrix
        from torch.utils.data import DataLoader
        from torchvision import datasets, models, transforms
    except Exception as exc:
        raise RuntimeError(
            "Could not import evaluation dependencies. Install them with:\n"
            "pip install -r requirements.txt"
        ) from exc

    return torch, confusion_matrix, DataLoader, datasets, models, transforms


def make_fixed_class_image_folder(datasets, class_names):
    class FixedClassImageFolder(datasets.ImageFolder):
        def find_classes(self, directory):
            return list(class_names), {class_name: index for index, class_name in enumerate(class_names)}

    return FixedClassImageFolder


def get_eval_transform(transforms, image_size: int):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def build_model(torch, models, num_classes: int):
    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = torch.nn.Linear(in_features, num_classes)
    return model


def print_confusion_matrix(matrix, class_names):
    header = "actual\\pred".ljust(14) + "".join(name[:10].rjust(12) for name in class_names)
    print(header)
    for class_name, row in zip(class_names, matrix):
        values = "".join(str(value).rjust(12) for value in row)
        print(class_name[:12].ljust(14) + values)


def prepare_misclassified_output_folder() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    MISCLASSIFIED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    for path in MISCLASSIFIED_IMAGES_DIR.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
            path.unlink()

    subfolders = [path for path in MISCLASSIFIED_IMAGES_DIR.rglob("*") if path.is_dir()]
    for folder in sorted(subfolders, key=lambda path: len(path.parts), reverse=True):
        try:
            folder.rmdir()
        except OSError:
            pass


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


def save_misclassified_examples(misclassified_examples: list[dict]) -> None:
    prepare_misclassified_output_folder()

    fieldnames = ["image_path", "actual_class", "predicted_class", "confidence"]
    with MISCLASSIFIED_CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(misclassified_examples)

    for example in misclassified_examples:
        source_path = Path(example["image_path"])
        folder_name = f"actual_{example['actual_class']}_pred_{example['predicted_class']}"
        destination_dir = MISCLASSIFIED_IMAGES_DIR / folder_name
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = unique_destination_path(destination_dir, source_path)
        shutil.copy2(source_path, destination_path)


def main() -> int:
    create_required_folders()

    if not MODEL_PATH.exists():
        print(f"Model file not found: {MODEL_PATH}")
        print("Train a model first with: python src/train.py")
        return 1

    try:
        validate_dataset_split("test", require_images=True, require_each_class=True)
    except DatasetError as exc:
        print(f"Dataset error:\n{exc}")
        return 1

    try:
        torch, confusion_matrix, DataLoader, datasets, models, transforms = load_evaluation_dependencies()
    except RuntimeError as exc:
        print(exc)
        return 1

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(MODEL_PATH, map_location=device)
    class_names = checkpoint.get("class_names", CLASS_NAMES)
    image_size = checkpoint.get("image_size", IMAGE_SIZE)

    model = build_model(torch, models, num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    FixedClassImageFolder = make_fixed_class_image_folder(datasets, class_names)
    test_dataset = FixedClassImageFolder(TEST_DIR, transform=get_eval_transform(transforms, image_size))
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    total_correct = 0
    total_examples = 0
    per_class_correct = {class_name: 0 for class_name in class_names}
    per_class_total = {class_name: 0 for class_name in class_names}
    all_predictions = []
    all_labels = []
    misclassified_examples = []
    dataset_index = 0

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)
            probabilities = torch.softmax(outputs, dim=1)
            predictions = torch.argmax(outputs, dim=1)
            confidences = probabilities.max(dim=1).values

            total_correct += (predictions == labels).sum().item()
            total_examples += labels.size(0)

            labels_list = labels.cpu().tolist()
            predictions_list = predictions.cpu().tolist()
            confidences_list = confidences.cpu().tolist()

            for label, prediction, confidence in zip(
                labels_list,
                predictions_list,
                confidences_list,
            ):
                actual_class = class_names[label]
                predicted_class = class_names[prediction]
                per_class_total[actual_class] += 1
                if label == prediction:
                    per_class_correct[actual_class] += 1
                else:
                    image_path = Path(test_dataset.samples[dataset_index][0])
                    misclassified_examples.append(
                        {
                            "image_path": str(image_path),
                            "actual_class": actual_class,
                            "predicted_class": predicted_class,
                            "confidence": f"{confidence:.4f}",
                        }
                    )

                all_labels.append(label)
                all_predictions.append(prediction)
                dataset_index += 1

    overall_accuracy = total_correct / max(total_examples, 1)
    print(f"Overall accuracy: {overall_accuracy:.4f}")

    print("\nPer-class accuracy:")
    for class_name in class_names:
        class_total = per_class_total[class_name]
        class_accuracy = per_class_correct[class_name] / max(class_total, 1)
        print(f"{class_name}: {class_accuracy:.4f} ({per_class_correct[class_name]}/{class_total})")

    matrix = confusion_matrix(
        all_labels,
        all_predictions,
        labels=list(range(len(class_names))),
    )
    print("\nConfusion matrix:")
    print_confusion_matrix(matrix, class_names)

    save_misclassified_examples(misclassified_examples)
    print("\nSaved misclassified examples to logs/misclassified.csv")
    print("Saved misclassified images to logs/misclassified_images/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
