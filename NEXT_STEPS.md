# Next Steps

This repo is ready for the next phase of the garbage sorting prototype.

## Current Status

- Python/PyTorch image classification prototype exists.
- Classes are `landfill`, `compost`, and `recycling`.
- MobileNetV3 Small is used for transfer learning.
- Hardware is simulated in `src/hardware_simulator.py`.
- Webcam mode automatically detects an object at the marked spot using OpenCV background-change detection, then classifies it.
- No real Raspberry Pi, STM32, actuators, motors, sensors, or chute are required yet.

## What To Do Next

1. Create a Python virtual environment.
2. Install `requirements.txt`.
3. Add real dataset images to `data/train`, `data/val`, and `data/test`.
4. Train with `python src/train.py`.
5. Evaluate with `python src/evaluate.py`.
6. Test one image with `python src/predict_image.py path/to/image.jpg`.
7. Test automatic webcam sorting with `python src/live_webcam.py`.

## Good Questions To Ask ChatGPT Next

- How many images should I collect per class for a first prototype?
- How should I split my dataset into train, validation, and test folders?
- How can I improve accuracy if compost and landfill get confused?
- Should I keep simple OpenCV object-present detection or switch to YOLO later?
- How would I connect this laptop prototype to a Raspberry Pi and STM32 later?
