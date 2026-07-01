# Garbage Sorter

This is a garbage sorting machine learning prototype for sorting trash item images into three classes:

- landfill
- compost
- recycling

It uses Python, PyTorch, torchvision, and MobileNetV3 Small transfer learning. The laptop workflow still works without any hardware, and the repo now also includes a hardware-ready Raspberry Pi/STM32 integration scaffold for future camera capture, serial commands, and simulated or real sorter hardware.

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

## Import Online Dataset

If you downloaded a waste dataset that already has class folders like `cans_all_type`, `glass_containers`, `paper_products`, `plastic_bottles`, `food_scraps`, `yard_trimmings`, `diapers`, or `styrofoam_product`, import it into this project's raw folders with:

```powershell
python src/import_online_dataset.py "C:\Users\shrey\Downloads\waste_dataset"
```

This does not download anything. It copies matching images from the local dataset folder into:

```text
data/raw/landfill/
data/raw/compost/
data/raw/recycling/
```

Common mappings:

- `cans_all_type`, `cans`, `aluminum_cans`, `metal_cans`, `glass_containers`, `paper_products`, `cardboard`, `plastic_bottles`, `plastic_containers` -> `recycling`
- `coffee_tea_bags`, `egg_shells`, `food_scraps`, `kitchen_waste`, `yard_trimmings`, `organic`, `biological`, `compost`, `food_waste`, `fruit`, `vegetable` -> `compost`
- `ceramic_product`, `diapers`, `sanitary_napkin`, `platics_bags_wrappers`, `plastics_bags_wrappers`, `plastic_bags_wrappers`, `stiroform_product`, `stroform_product`, `styrofoam_product`, `foam`, `trash`, `garbage`, `non-recyclable` -> `landfill`

Classes such as `batteries`, `battery`, `e-waste`, `electronics`, `paints`, `pesticides`, `hazardous`, `medical`, and `unknown` are ignored.

To limit how many images are copied into each final class:

```powershell
python src/import_online_dataset.py "C:\Users\shrey\Downloads\waste_dataset" --max-per-class 300
```

When `--max-per-class` is used, the importer balances the copied images across the matching source class folders instead of filling a final class from only the first matching folder.

To clear existing images from `data/raw` before importing:

```powershell
python src/import_online_dataset.py "C:\Users\shrey\Downloads\waste_dataset" --max-per-class 300 --clear-existing
```

After importing, check image counts with:

```powershell
python src/dataset_report.py
```

## Collect Camera Images

You can also collect real images directly into `data/raw` with a laptop webcam, USB camera, or Raspberry Pi camera.

OpenCV laptop/USB camera mode:

```powershell
python src/collect_pi_images.py --class recycling
python src/collect_pi_images.py --class compost
python src/collect_pi_images.py --class landfill
```

In OpenCV mode, a preview window opens.

- Press `SPACE` to capture an image.
- Press `q` to quit.

Images are saved as:

```text
data/raw/recycling/recycling_pi_000001.jpg
data/raw/compost/compost_pi_000001.jpg
data/raw/landfill/landfill_pi_000001.jpg
```

To use a different OpenCV camera index:

```powershell
python src/collect_pi_images.py --class recycling --camera opencv --camera-index 1
```

On a Raspberry Pi with Picamera2 installed:

```powershell
python src/collect_pi_images.py --class recycling --camera picamera2
```

Picamera2 mode uses an Enter-to-capture fallback if a preview window is not available.

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

## Sorter Runner

`src/run_sorter.py` is the simulation-first main app for the future Raspberry Pi sorter. It uses the trained ML model, applies the confidence threshold, logs predictions, and sends accepted predictions to either simulated hardware or serial hardware.

Run with an existing saved image and simulated hardware:

```powershell
python src/run_sorter.py --hardware sim --image data/test/recycling/example.jpg
```

Run with simulated hardware and OpenCV camera capture:

```powershell
python src/run_sorter.py --hardware sim --camera opencv
```

Future Raspberry Pi mode with Picamera2 and STM32 serial hardware:

```powershell
python src/run_sorter.py --hardware serial --camera picamera2
```

When `--image` is provided, no camera is required.

## Hardware Integration Docs

- [Hardware Bringup](docs/HARDWARE_BRINGUP.md)
- [Serial Protocol](docs/SERIAL_PROTOCOL.md)
- [Raspberry Pi Setup](docs/RASPBERRY_PI_SETUP.md)
- [STM32 Integration Plan](docs/STM32_INTEGRATION_PLAN.md)

## Hardware Diagnostics

Use `src/hardware_diagnostics.py` to test the software, camera, simulator, and STM32 serial path one piece at a time.

```powershell
python src/hardware_diagnostics.py --check-model
python src/hardware_diagnostics.py --image data/test/recycling/example.jpg
python src/hardware_diagnostics.py --check-camera --camera opencv
python src/hardware_diagnostics.py --check-camera --camera picamera2
python src/hardware_diagnostics.py --check-sim
python src/hardware_diagnostics.py --check-serial-ping --port COM3
python src/hardware_diagnostics.py --check-serial-ping --port /dev/ttyACM0
python src/hardware_diagnostics.py --check-serial-sort recycling --port COM3
python src/hardware_diagnostics.py --full-sim --image data/test/recycling/example.jpg
```

Run serial sort diagnostics only with motors disconnected or STM32 dry-run firmware.

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
