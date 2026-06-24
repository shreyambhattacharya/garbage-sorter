import sys

from config import (
    BATCH_SIZE,
    CLASS_NAMES,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    LEARNING_RATE,
    MODEL_PATH,
    MODELS_DIR,
    NUM_EPOCHS,
    TRAIN_DIR,
    VAL_DIR,
)
from dataset_utils import DatasetError, create_required_folders, validate_dataset_split


def load_training_dependencies():
    try:
        import torch
        from torch import nn
        from torch.utils.data import DataLoader
        from torchvision import datasets, models, transforms
        from tqdm.auto import tqdm
    except Exception as exc:
        raise RuntimeError(
            "Could not import the training dependencies. Install them with:\n"
            "pip install -r requirements.txt"
        ) from exc

    return torch, nn, DataLoader, datasets, models, transforms, tqdm


def make_fixed_class_image_folder(datasets):
    class FixedClassImageFolder(datasets.ImageFolder):
        def find_classes(self, directory):
            return list(CLASS_NAMES), {class_name: index for index, class_name in enumerate(CLASS_NAMES)}

    return FixedClassImageFolder


def get_transforms(transforms):
    train_transform = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )

    eval_transform = transforms.Compose(
        [
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )

    return train_transform, eval_transform


def build_model(nn, models, num_classes: int):
    weights = None
    weights_enum = getattr(models, "MobileNet_V3_Small_Weights", None)
    if weights_enum is not None:
        weights = weights_enum.DEFAULT

    try:
        model = models.mobilenet_v3_small(weights=weights)
        if weights is not None:
            print("Loaded MobileNetV3 Small with pretrained ImageNet weights.")
    except Exception as exc:
        print(f"Pretrained weights are not available ({exc}).")
        print("Using MobileNetV3 Small with randomly initialized weights.")
        model = models.mobilenet_v3_small(weights=None)

    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def train_one_epoch(model, data_loader, criterion, optimizer, device, torch, tqdm):
    model.train()
    running_loss = 0.0
    total_examples = 0

    progress = tqdm(data_loader, desc="Training", leave=False)
    for images, labels in progress:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        batch_size = images.size(0)
        running_loss += loss.item() * batch_size
        total_examples += batch_size
        progress.set_postfix(loss=f"{loss.item():.4f}")

    return running_loss / max(total_examples, 1)


def validate(model, data_loader, criterion, device, torch, tqdm):
    model.eval()
    running_loss = 0.0
    correct = 0
    total_examples = 0

    progress = tqdm(data_loader, desc="Validation", leave=False)
    with torch.no_grad():
        for images, labels in progress:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)
            predictions = torch.argmax(outputs, dim=1)

            batch_size = images.size(0)
            running_loss += loss.item() * batch_size
            correct += (predictions == labels).sum().item()
            total_examples += batch_size

    avg_loss = running_loss / max(total_examples, 1)
    accuracy = correct / max(total_examples, 1)
    return avg_loss, accuracy


def main() -> int:
    create_required_folders()

    try:
        validate_dataset_split("train", require_images=True, require_each_class=True)
        validate_dataset_split("val", require_images=True, require_each_class=True)
    except DatasetError as exc:
        print(f"Dataset error:\n{exc}")
        return 1

    try:
        torch, nn, DataLoader, datasets, models, transforms, tqdm = load_training_dependencies()
    except RuntimeError as exc:
        print(exc)
        return 1

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_transform, eval_transform = get_transforms(transforms)
    FixedClassImageFolder = make_fixed_class_image_folder(datasets)

    train_dataset = FixedClassImageFolder(TRAIN_DIR, transform=train_transform)
    val_dataset = FixedClassImageFolder(VAL_DIR, transform=eval_transform)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    model = build_model(nn, models, num_classes=len(CLASS_NAMES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    best_val_accuracy = -1.0
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, NUM_EPOCHS + 1):
        print(f"\nEpoch {epoch}/{NUM_EPOCHS}")
        train_loss = train_one_epoch(model, train_loader, criterion, optimizer, device, torch, tqdm)
        val_loss, val_accuracy = validate(model, val_loader, criterion, device, torch, tqdm)

        print(f"Training loss: {train_loss:.4f}")
        print(f"Validation loss: {val_loss:.4f}")
        print(f"Validation accuracy: {val_accuracy:.4f}")

        if val_accuracy > best_val_accuracy:
            best_val_accuracy = val_accuracy
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "class_names": CLASS_NAMES,
                    "image_size": IMAGE_SIZE,
                    "validation_accuracy": best_val_accuracy,
                },
                MODEL_PATH,
            )
            print(f"Saved best model to: {MODEL_PATH}")

    if not MODEL_PATH.exists():
        print("Training finished, but no model was saved. Check your validation data.")
        return 1

    print(f"\nBest validation accuracy: {best_val_accuracy:.4f}")
    print(f"Model saved at: {MODEL_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
