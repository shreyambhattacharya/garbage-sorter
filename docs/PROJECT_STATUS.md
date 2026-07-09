# Project Status

This document summarizes the current engineering state of the Garbage Sorter repo. It is intentionally honest: the project has a working embedded ML control path and verified servo bring-up, but it does not claim final physical sorting reliability yet.

## Resume Status Table

| Area | Status | Evidence / Command |
| --- | --- | --- |
| Python ML pipeline | Implemented | `python src/train.py`, `python src/evaluate.py --save-confusion-matrix --save-summary` |
| Dataset import and splitting | Implemented | `python src/import_online_dataset.py <dataset_path>`, `python src/prepare_dataset.py --clear-existing` |
| Simulation mode | Implemented | `python src/hardware_diagnostics.py --check-sim` |
| Main sorter runner | Implemented | `python src/run_sorter.py --hardware sim --image data/test/recycling/example.jpg` |
| Python serial protocol | Implemented | `python -m pytest tests/test_serial_protocol.py` |
| STM32 serial communication | Verified locally on `COM6` | `python src/hardware_diagnostics.py --check-serial-ping --port COM6` |
| STM32 `PING`/`STATUS`/`RESET`/`SORT` protocol | Implemented | PuTTY at `COM6`, `115200` baud; send `PING`, `STATUS`, `RESET`, `SORT class=recycling confidence=0.9000 id=1` |
| Servo PWM control | Implemented locally; verify after each flash | TIM3 CH1-CH4 configured at 20 ms period and 1500 us initial pulse |
| Diverter test command | Implemented locally | `python src/hardware_diagnostics.py --test-diverters --port COM6` |
| Trapdoor test command | Implemented locally | `python src/hardware_diagnostics.py --test-trapdoor --port COM6` |
| Full physical sort | In progress | Run repeated `SORT` trials after mechanical calibration |
| Ultrasonic bin fullness sensors | Scaffolded, not verified | `TEST_ULTRASONIC` should return a clear not-configured response |
| SPI TFT display | Scaffolded, not verified | `TEST_DISPLAY` should return a clear not-configured response |
| Results artifacts | Pending real run | Generate `results/evaluation_summary.md`, `results/confusion_matrix.png`, and latency summaries |
| Demo media | Missing | Record and add final bench demo media only after verified physical tests |

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
- Raspberry Pi camera-to-STM32 deployment path.

These pieces are intentionally guarded by subsystem flags until the hardware is configured and tested.

## What Remains

- Final mechanical linkage calibration.
- Repeated route testing for landfill, compost, and recycling.
- Ultrasonic trigger/echo GPIO setup and voltage-safe wiring.
- TFT controller confirmation and display-driver implementation.
- Full closed-loop physical sorting reliability testing.
- Final evaluation and latency artifacts from the current dataset/model.
- Demo media from a verified bench run.

## Before Resume Use

- Generate real evaluation artifacts with `python src/evaluate.py --save-confusion-matrix --save-summary`.
- Generate real latency artifacts with `python src/measure_latency.py --port COM6 --image data/test/recycling/example.jpg --class recycling --trials 30`.
- Add final demo media only after the physical bench setup is working reliably.
- Keep accuracy and latency claims tied to committed artifacts in `results/`.
- Re-run serial ping, diverter test, trapdoor test, and at least one `SORT` command after flashing STM32 firmware.
- Confirm no generated build outputs, datasets, model weights, logs, or captured images are staged.

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
- No final published latency number is claimed in the repo.
- Ultrasonic sensors are not yet verified.
- TFT display is not yet verified.
- Full physical sorting reliability is still in progress and depends on mechanical calibration.
- Servo tests should be run no-load before attaching the mechanism.

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
