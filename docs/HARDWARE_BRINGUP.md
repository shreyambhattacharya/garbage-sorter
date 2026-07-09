# Hardware Bringup

This project is being brought up in small, testable hardware milestones. The current verified hardware milestone is Python-to-STM32 serial communication plus four-servo PWM bring-up. Ultrasonic bin sensors and the SPI TFT display are still future bring-up work.

## Bring-Up Sequence

1. Serial ping
2. Servo PWM no-load test
3. `TEST_DIVERTERS` no-load
4. `TEST_TRAPDOOR` no-load
5. Mechanical calibration
6. `SORT` command with servos
7. Ultrasonic setup
8. TFT setup
9. Full closed-loop physical demo

## Recommended Diagnostics

Use `src/hardware_diagnostics.py` before attaching the servos to the mechanism:

```powershell
python src/hardware_diagnostics.py --check-model
python src/hardware_diagnostics.py --check-sim
python src/hardware_diagnostics.py --check-serial-ping --port COM6
python src/hardware_diagnostics.py --test-diverters --port COM6
python src/hardware_diagnostics.py --test-trapdoor --port COM6
python src/hardware_diagnostics.py --check-serial-sort recycling --port COM6
```

Use `/dev/ttyACM0` or your actual serial device on Linux/Raspberry Pi.

## Phase 1: Raspberry Pi Setup

- Clone the repo onto the Raspberry Pi.
- Create a Python virtual environment.
- Install the Python requirements.
- Confirm the trained model file exists at `models/garbage_classifier.pt`.
- Run the sorter in simulation mode before trying serial hardware.

## Phase 2: Camera Test

- Test the camera by itself before using the sorter runner.
- For USB or laptop-style cameras, start with OpenCV mode.
- For Raspberry Pi camera modules, use Picamera2 only after Raspberry Pi OS camera setup is working.
- Collect a few images and inspect them manually for focus, lighting, framing, and glare.

## Phase 3: ML Inference On Pi

- Run prediction on saved images before using live camera capture.
- Confirm the model loads successfully on the Pi.
- Confirm class probabilities look reasonable.
- Confirm uncertain predictions do not trigger hardware commands.

Useful first command:

```bash
python src/run_sorter.py --hardware sim --image data/test/recycling/example.jpg
```

## Phase 4: STM32 Serial Test

- Test serial communication before connecting servo power.
- Start with `PING` and expect `PONG`.
- Run `STATUS` and confirm the state is readable.
- Run `RESET` and confirm the state returns to `IDLE`.

## Phase 5: Servo Bring-Up

- Do not power servos from Raspberry Pi or STM32 GPIO.
- Use an external 5-6 V servo supply.
- Connect external servo ground to STM32 ground.
- Test PWM with servos disconnected from the mechanism first.
- Run `TEST_DIVERTERS` no-load.
- Run `TEST_TRAPDOOR` no-load.
- Adjust pulse widths in `sorter_hardware_config.h`.

## Phase 6: Servo Sort Command

- Run `SORT class=recycling confidence=0.9000 id=1` only after no-load servo tests pass.
- Confirm `ACK id=1` arrives before motion completes.
- Confirm `DONE id=1` arrives only after the diverter/trapdoor sequence completes.
- Repeat with landfill, recycling, and compost routes.

## Phase 7: Sensor Test

Ultrasonic sensors are scaffolded but not yet verified.

- Configure trigger/echo pins in CubeIDE.
- Confirm voltage compatibility for echo pins before wiring.
- Enable `SORTER_ULTRASONIC_ENABLED` only after GPIO setup is correct.
- Verify timeouts with disconnected and blocked sensors.

## Phase 8: TFT Test

The TFT display abstraction is scaffolded but not yet verified.

- Confirm the TFT controller before writing the final driver.
- Configure SPI and control pins in CubeIDE.
- Enable `SORTER_TFT_ENABLED` only after SPI/control pin setup is correct.

## Software Checklist

- `python -m pytest` passes.
- `python src/hardware_diagnostics.py --check-serial-ping --port COM6` passes.
- `python src/hardware_diagnostics.py --test-diverters --port COM6` passes.
- `python src/hardware_diagnostics.py --test-trapdoor --port COM6` passes.
- README current status is accurate.
- No generated build artifacts are committed.

## Safety Notes

- Do not power servos from Raspberry Pi or STM32 GPIO.
- Verify external servo power before attaching linkages.
- Verify common ground between external servo supply and STM32.
- Test servos disconnected from the mechanism first.
- Start with conservative pulse widths.
- Use one item at a time during first full physical tests.
