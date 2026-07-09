# Project Status

This document summarizes the current state of the Garbage Sorter repo.

## What Works Now

- Python image classification pipeline for landfill, compost, and recycling.
- Dataset import and train/validation/test splitting tools.
- Model training, evaluation, single-image prediction, and webcam/laptop demos.
- Simulation-first sorter runner.
- Python serial protocol support.
- Python hardware diagnostics for model, simulator, serial ping, serial sort, and STM32 servo bring-up commands.
- STM32 USART2 serial communication at `115200` baud.
- STM32 `PING`, `STATUS`, `RESET`, and `SORT` protocol handling.
- STM32 TIM3 PWM outputs for four servos.
- STM32 `TEST_DIVERTERS` and `TEST_TRAPDOOR` servo bring-up commands.

## What Is Scaffolded

- Ultrasonic bin fullness sensor module.
- SPI TFT display abstraction.
- Bin-full warning flow.
- Full Raspberry Pi camera-to-STM32 sorter runner path.

These pieces are intentionally guarded by subsystem flags until the hardware is configured and tested.

## What Remains

- Final mechanical linkage calibration.
- Repeated route testing for landfill, compost, and recycling.
- Ultrasonic trigger/echo GPIO setup and voltage-safe wiring.
- TFT controller confirmation and display-driver implementation.
- Full closed-loop physical sorting reliability testing.

## Demo Reproduction

Python-only:

```powershell
python src/hardware_diagnostics.py --check-sim
python src/run_sorter.py --hardware sim --image data/test/recycling/example.jpg
```

STM32 serial and servo bring-up:

```powershell
python src/hardware_diagnostics.py --check-serial-ping --port COM6
python src/hardware_diagnostics.py --test-diverters --port COM6
python src/hardware_diagnostics.py --test-trapdoor --port COM6
python src/hardware_diagnostics.py --check-serial-sort recycling --port COM6
```

Evaluation artifacts:

```powershell
python src/evaluate.py --save-confusion-matrix --save-summary
```

Latency artifacts:

```powershell
python src/measure_latency.py --port COM6 --image data/test/recycling/example.jpg --class recycling --trials 30
```

Unit tests:

```powershell
python -m pytest
```

## Known Limitations

- No final published model accuracy is claimed in the repo.
- Ultrasonic sensors are not yet verified.
- TFT display is not yet verified.
- Full physical sorting reliability is still in progress and depends on mechanical calibration.
- Servo tests should be run no-load before attaching the mechanism.
- README result tables are placeholders until `results/evaluation_summary.md`, `results/confusion_matrix.png`, and `results/latency_summary.md` are generated from current runs.

## GitHub Metadata Reminder

Codex cannot reliably set GitHub repository metadata from code. Set these manually in the GitHub repo settings.

Suggested description:

```text
Embedded ML garbage sorter using Raspberry Pi image classification and STM32 servo control for physical landfill/compost/recycling routing.
```

Suggested topics:

```text
embedded-systems
machine-learning
computer-vision
stm32
raspberry-pi
pytorch
uart
servo-control
robotics
waste-sorting
```
