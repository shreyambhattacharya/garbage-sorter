import argparse
import sys
from pathlib import Path

from config import (
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    MODEL_PATH,
    PROJECT_ROOT,
)


class PredictionError(RuntimeError):
    """Raised when a prediction cannot be completed."""


def load_prediction_dependencies():
    try:
        import torch
        from PIL import Image
        from torchvision import models, transforms
    except Exception as exc:
        raise PredictionError(
            "Could not import prediction dependencies. Install them with:\n"
            "pip install -r requirements.txt"
        ) from exc

    return torch, Image, models, transforms


def resolve_path(path_text: str | Path) -> Path:
    path = Path(str(path_text).strip().strip('"').strip("'"))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def build_model(torch, models, num_classes: int):
    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = torch.nn.Linear(in_features, num_classes)
    return model


def get_eval_transform(transforms, image_size: int = IMAGE_SIZE):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def load_model(model_path: Path = MODEL_PATH) -> dict:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Train a model first with: python src/train.py"
        )

    torch, Image, models, transforms = load_prediction_dependencies()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    try:
        checkpoint = torch.load(model_path, map_location=device)
    except Exception as exc:
        raise PredictionError(f"Could not load model checkpoint: {model_path}") from exc

    if "model_state_dict" not in checkpoint:
        raise PredictionError(
            f"Invalid checkpoint: {model_path}\n"
            "Expected the key 'model_state_dict'. Train a new model with python src/train.py."
        )

    class_names = checkpoint.get("class_names", CLASS_NAMES)
    image_size = checkpoint.get("image_size", IMAGE_SIZE)

    model = build_model(torch, models, num_classes=len(class_names))
    try:
        model.load_state_dict(checkpoint["model_state_dict"])
    except Exception as exc:
        raise PredictionError("Checkpoint weights do not match the MobileNetV3 model.") from exc
    model.to(device)
    model.eval()

    return {
        "model": model,
        "class_names": class_names,
        "image_size": image_size,
        "device": device,
        "torch": torch,
        "Image": Image,
        "transforms": transforms,
    }


def predict_pil_image(image, model_bundle: dict) -> dict:
    torch = model_bundle["torch"]
    transforms = model_bundle["transforms"]
    model = model_bundle["model"]
    device = model_bundle["device"]
    class_names = model_bundle["class_names"]
    image_size = model_bundle["image_size"]

    transform = get_eval_transform(transforms, image_size=image_size)
    image_tensor = transform(image.convert("RGB")).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(image_tensor)
        probabilities_tensor = torch.softmax(logits, dim=1)[0].detach().cpu()

    probabilities = {
        class_name: float(probabilities_tensor[index].item())
        for index, class_name in enumerate(class_names)
    }
    predicted_class = max(probabilities, key=probabilities.get)
    confidence = probabilities[predicted_class]
    decision = "ACCEPT" if confidence >= CONFIDENCE_THRESHOLD else "UNCERTAIN"

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": probabilities,
        "decision": decision,
    }


def predict_image_path(image_path: str | Path, model_bundle: dict | None = None) -> dict:
    resolved_path = resolve_path(image_path)
    if not resolved_path.exists():
        raise FileNotFoundError(f"Image file not found: {resolved_path}")
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Expected an image file but found a folder: {resolved_path}")

    bundle = model_bundle or load_model()
    Image = bundle["Image"]

    try:
        with Image.open(resolved_path) as image:
            result = predict_pil_image(image, bundle)
    except PredictionError:
        raise
    except Exception as exc:
        raise PredictionError(f"Could not open or classify image: {resolved_path}") from exc

    result["image_path"] = resolved_path
    return result


def print_prediction_result(result: dict) -> None:
    print(f"Prediction: {result['predicted_class']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print("\nClass probabilities:")

    probabilities = result["probabilities"]
    for class_name in probabilities:
        print(f"{class_name}: {probabilities[class_name]:.2f}")

    print(f"\nDecision: {result['decision']}")


def parse_args():
    parser = argparse.ArgumentParser(description="Predict the garbage class for one image.")
    parser.add_argument("image_path", help="Path to an image file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        result = predict_image_path(args.image_path)
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        print(f"Prediction error:\n{exc}")
        return 1

    print_prediction_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
