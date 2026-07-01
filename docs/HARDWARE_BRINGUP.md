# Hardware Bringup

This project should move from laptop-only simulation to Raspberry Pi + STM32 hardware in small, testable phases. Test each component by itself before connecting the full system.

## Recommended Diagnostics Order

Use `src/hardware_diagnostics.py` before connecting real actuators:

1. Run `python src/hardware_diagnostics.py --check-model`.
2. Run `python src/hardware_diagnostics.py --image data/test/recycling/example.jpg` with a known test image.
3. Run `python src/hardware_diagnostics.py --check-camera --camera opencv` or `python src/hardware_diagnostics.py --check-camera --camera picamera2`.
4. Run `python src/hardware_diagnostics.py --check-sim`.
5. Run `python src/hardware_diagnostics.py --check-serial-ping --port COM3` or `python src/hardware_diagnostics.py --check-serial-ping --port /dev/ttyACM0` with the STM32 connected.
6. Run `python src/hardware_diagnostics.py --check-serial-sort recycling --port COM3` only with motors disconnected or STM32 dry-run firmware.
7. Only then test actuators separately.

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

- Test serial communication before motors, actuators, or sensors are connected.
- Start with `PING` and expect `PONG`.
- Then test `STATUS`.
- Then test `SORT` with the actuator outputs disconnected or disabled.
- Confirm the STM32 sends `ACK` quickly and `DONE` only when the simulated or real motion sequence is complete.

## Phase 5: Actuator Test

- Do not power motors from Raspberry Pi GPIO.
- Use an external motor or actuator power supply sized for the load.
- Verify common ground between control electronics and motor driver when the circuit requires it.
- Test motors disconnected from the chute or trapdoor mechanism first.
- Confirm direction, limit behavior, current draw, and emergency stop behavior before attaching the mechanism.

## Phase 6: Sensor Test

- Test ultrasonic sensors independently.
- Verify sensor readings are stable with no item, one item, and a blocked path.
- Confirm the STM32 handles sensor timeouts or invalid readings safely.
- Do not let a missing sensor reading keep a motor running indefinitely.

## Phase 7: Integrated Dry Run

- Run `--hardware sim` with the trained model first.
- Then run serial mode with motors disabled.
- Confirm commands, acknowledgements, state transitions, logs, and failure messages.
- Confirm uncertain predictions do not move hardware.

## Phase 8: Full System Test

- Use one item at a time during first full tests.
- Keep the mechanism accessible and easy to power down.
- Verify the chute starts in a known home position.
- Verify trapdoor open and close timing.
- Watch for jams, false triggers, unstable sensor readings, and repeated commands.
- Increase test complexity only after individual components are reliable.

## Safety Notes

- Do not power motors from Raspberry Pi GPIO.
- Verify external motor power before attaching actuators.
- Verify common ground where required by the motor driver and serial wiring.
- Test motors disconnected from the mechanism first.
- Run simulation mode before serial mode.
- Use one item at a time during first full system tests.
