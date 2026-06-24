import sys
from pathlib import Path

from config import MODEL_PATH, PROJECT_ROOT
from dataset_utils import log_prediction
from hardware_simulator import send_sort_command
from predict_image import (
    PredictionError,
    load_model,
    predict_image_path,
    print_prediction_result,
)


def resolve_user_path(path_text: str) -> Path:
    path = Path(path_text.strip().strip('"').strip("'"))
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def main() -> int:
    if not MODEL_PATH.exists():
        print(f"Model file not found: {MODEL_PATH}")
        print("Train a model first with: python src/train.py")
        return 1

    try:
        model_bundle = load_model()
    except (FileNotFoundError, KeyError, PredictionError) as exc:
        print(f"Could not load model:\n{exc}")
        return 1

    print("Garbage Sorter laptop demo")
    print("Enter an image path, or type q to quit.")

    while True:
        user_input = input("\nImage path: ").strip()
        if user_input.lower() in {"q", "quit"}:
            print("Goodbye.")
            return 0
        if not user_input:
            print("Please enter an image path, or q to quit.")
            continue

        image_path = resolve_user_path(user_input)
        if not image_path.exists():
            print(f"Image file not found: {image_path}")
            continue

        try:
            result = predict_image_path(image_path, model_bundle=model_bundle)
        except (FileNotFoundError, PredictionError) as exc:
            print(f"Prediction error:\n{exc}")
            continue

        print_prediction_result(result)
        log_prediction(
            result["image_path"],
            result["predicted_class"],
            result["confidence"],
            result["decision"],
        )

        if result["decision"] == "ACCEPT":
            send_sort_command(result["predicted_class"], result["confidence"])
        else:
            print("Please reposition item or sort manually.")


if __name__ == "__main__":
    sys.exit(main())
