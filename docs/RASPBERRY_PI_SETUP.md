# Raspberry Pi Setup

These steps prepare a Raspberry Pi to run the garbage sorter software. They avoid assumptions about the exact Pi model.

## Clone The Repo

```bash
git clone https://github.com/shreyambhattacharya/garbage-sorter.git
cd garbage-sorter
```

## Create A Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If PyTorch installation needs a Pi-specific wheel or index, follow the current official PyTorch installation guidance for the OS and Python version you are using.

## Camera Setup

OpenCV mode can work with many USB cameras:

```bash
python src/collect_pi_images.py --class recycling --camera opencv
```

Picamera2 mode may require Raspberry Pi OS camera setup before this project can use it. Confirm the camera works with Raspberry Pi OS camera tools first, then try:

```bash
python src/collect_pi_images.py --class recycling --camera picamera2
```

## Run Model Inference

First confirm a trained model checkpoint exists:

```text
models/garbage_classifier.pt
```

Then run prediction on a saved image:

```bash
python src/predict_image.py data/test/recycling/example.jpg
```

## Run Sorter In Simulation Mode First

Use simulation mode before connecting serial hardware:

```bash
python src/run_sorter.py --hardware sim --image data/test/recycling/example.jpg
```

With camera capture:

```bash
python src/run_sorter.py --hardware sim --camera opencv
```

## Then Run Serial Mode

After the STM32 serial firmware is ready and tested independently:

```bash
python src/serial_hardware.py --port /dev/ttyACM0 --ping
```

Then try the sorter with serial hardware:

```bash
python src/run_sorter.py --hardware serial --camera picamera2 --serial-port /dev/ttyACM0
```

Run serial mode only after simulation mode, camera capture, and saved-image inference all work.
