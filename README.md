# Garbage Sorter

This is a laptop-only machine learning prototype for sorting trash item images into three classes:

- landfill
- compost
- recycling

It uses Python, PyTorch, torchvision, and MobileNetV3 Small transfer learning. No Raspberry Pi, STM32, camera hardware, motors, actuators, chute, or ultrasonic sensor is required yet. The hardware behavior is simulated in code.

## Project Structure

```text
Garbage Sorter/
  README.md
  requirements.txt
  data/
    raw/
      landfill/
      compost/
      recycling/
    train/
      landfill/
      compost/
      recycling/
    val/
      landfill/
      compost/
      recycling/
    test/
      landfill/
      compost/
      recycling/
  models/
  logs/
  src/
```

## Windows Setup

Open PowerShell in VS Code and run commands from the project folder. Because the folder name contains a space, keep the path in quotes.

```powershell
cd "$env:USERPROFILE\Desktop\Projects\Garbage Sorter"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If your Desktop is managed by OneDrive, the folder may be here instead:

```powershell
cd "$env:USERPROFILE\OneDrive\Desktop\Projects\Garbage Sorter"
```

## Add Dataset Images

Put your unsplit raw images into these folders:

```text
data/raw/landfill/
data/raw/compost/
data/raw/recycling/
```

Supported image formats are `.jpg`, `.jpeg`, `.png`, `.bmp`, and `.webp`.

Do not put all images into one folder. The folder name is how the training script learns the label.

## Prepare Dataset

Run this command to copy raw images into an 80/10/10 train/validation/test split:

```powershell
python src/prepare_dataset.py --clear-existing
```

This creates copied images in:

```text
data/train/landfill/
data/train/compost/
data/train/recycling/

data/val/landfill/
data/val/compost/
data/val/recycling/

data/test/landfill/
data/test/compost/
data/test/recycling/
```

Raw images are not moved or deleted. The split is shuffled with a fixed seed so it is reproducible.

Optional split settings:

```powershell
python src/prepare_dataset.py --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1 --seed 42 --clear-existing
```

## Train

```powershell
python src/train.py
```

The training script loads images from `data/train` and `data/val`, applies image augmentation to training images, and saves the best checkpoint to:

```text
models/garbage_classifier.pt
```

The checkpoint stores the model weights, class names, image size, and validation accuracy.

## Evaluate

```powershell
python src/evaluate.py
```

This evaluates the saved model on `data/test`, then prints overall accuracy, per-class accuracy, and a confusion matrix.

## Predict One Image

```powershell
python src/predict_image.py data/test/recycling/example.jpg
```

Example output:

```text
Prediction: recycling
Confidence: 0.91

Class probabilities:
landfill: 0.03
compost: 0.06
recycling: 0.91

Decision: ACCEPT
```

## Laptop App

```powershell
python src/app.py
```

The app repeatedly asks for an image path. It classifies the image, prints the probabilities, logs the prediction to `logs/predictions.csv`, and sends an accepted result to the hardware simulator.

Type `q` or `quit` to exit.

## Webcam Demo

```powershell
python src/live_webcam.py
```

The webcam demo opens your laptop camera and runs automatically.

- Keep the marked spot empty for the first few seconds while the background calibrates.
- Place one item on the marked spot.
- The app detects that an object is present, classifies it, logs the result, and runs the simulated hardware command if the prediction is accepted.
- Remove the item after sorting so the system can reset for the next item.
- Press `Q` to quit.

If the prediction is accepted, the simulated STM32 command sequence is printed.

This uses simple OpenCV background-change detection to decide whether something is sitting in the marked spot. It is not YOLO and it does not draw bounding boxes; it only triggers classification when the marked area changes enough and stays stable.

## Confidence Threshold

The confidence threshold is set to `0.80` in `src/config.py`.

- If confidence is at least `0.80`, the decision is `ACCEPT`.
- If confidence is below `0.80`, the decision is `UNCERTAIN`.

For uncertain predictions, the app prints:

```text
Please reposition item or sort manually.
```

## Hardware Simulation

This prototype does not control real hardware. `src/hardware_simulator.py` simulates the future STM32 behavior:

```text
Sending command to STM32: SORT recycling CONF=0.91
STM32: ACK
STM32: rotating chute to recycling bin
STM32: opening trapdoor
STM32: sorting complete
```

Later, the same `send_sort_command(class_name, confidence)` function can be replaced or extended to send serial commands from a Raspberry Pi to an STM32.

## Notes

- This project is image classification only.
- It does not use YOLO or bounding-box object detection.
- The webcam demo uses a simple OpenCV object-present trigger before classification.
- It does not create fake training images.
- It does not download a dataset automatically.
- Training will stop with a clear message if the dataset folders are empty.
