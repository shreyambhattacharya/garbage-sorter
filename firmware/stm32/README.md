# STM32 Firmware

This folder contains the STM32CubeIDE firmware project for the Garbage Sorter STM32 side.

The current firmware keeps the existing serial protocol and adds a hardware-control architecture for servos, ultrasonic bin sensors, and an SPI TFT display. The real hardware mappings are centralized in one file so breadboard wiring can change without scattering pin edits through the code.

## Hardware

- Board: NUCLEO-F446RE
- IDE: STM32CubeIDE
- UART: USART2
- Baud rate: 115200
- Windows development serial port: COM6

## Current Milestone

The STM32 currently supports:

- UART command parsing and validation
- State tracking
- `PING`, `STATUS`, `RESET`, and `SORT`
- Manual hardware bring-up commands
- A centralized hardware configuration header
- Hardware abstraction modules for four servos, three ultrasonic sensors, and one SPI TFT display

The hardware modules are intentionally disabled by default because the current `.ioc` only has USART2 and basic NUCLEO GPIO configured. The firmware does not claim working motor/servo/sensor/display control until CubeIDE generates the required PWM, GPIO, and SPI peripherals.

## Central Hardware Configuration

Edit this file after deciding final wiring:

```text
Core/Inc/sorter_hardware_config.h
```

It contains:

- Servo timer/channel mappings
- Ultrasonic trigger/echo GPIO mappings
- TFT SPI/control pin mappings
- Servo pulse-width calibration values
- Diverter route table
- Ultrasonic bin-full threshold
- Safety delays

Important switches:

```c
#define SORTER_HARDWARE_ENABLED 0
#define SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP 1
```

Leave `SORTER_HARDWARE_ENABLED` at `0` until CubeIDE has generated the required peripherals. After CubeIDE setup and pin-map edits are complete, set:

```c
#define SORTER_HARDWARE_ENABLED 1
#define SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP 0
```

If hardware is enabled while the setup guard is still active, the build stops with a clear error.

## Servo Safety

Do not power servos from STM32 GPIO pins.

Use an external 5-6 V servo supply and connect the external supply ground to STM32 ground. Keep the first tests unloaded or disconnected from the mechanism.

Servo pulse values are configured in microseconds:

```c
#define SERVO_MIN_PULSE_US 1000U
#define SERVO_CENTER_PULSE_US 1500U
#define SERVO_MAX_PULSE_US 2000U
```

Start with conservative values, then adjust these route/calibration macros:

```c
DIVERTER_1_LEFT_US
DIVERTER_1_RIGHT_US
DIVERTER_2_LEFT_US
DIVERTER_2_RIGHT_US
TRAPDOOR_LEFT_CLOSED_US
TRAPDOOR_LEFT_OPEN_US
TRAPDOOR_RIGHT_CLOSED_US
TRAPDOOR_RIGHT_OPEN_US
```

The timer PWM setup should use a 50 Hz servo period and a 1 us timer tick so a compare value of `1500` means a 1500 us pulse.

## Routing

The two-binary-diverter route table is centralized in `sorter_hardware_config.h`.

Default logical routing:

```text
landfill  -> diverter 1 LEFT,  diverter 2 LEFT
recycling -> diverter 1 RIGHT, diverter 2 LEFT
compost   -> diverter 1 RIGHT, diverter 2 RIGHT
```

If a servo direction is reversed mechanically, edit the route macros in the config header instead of changing `sorter_hardware.c`.

## Ultrasonic Bin Warnings

Each ultrasonic sensor points downward into a bin. If the measured distance to the trash surface is below:

```c
#define BIN_ALMOST_FULL_DISTANCE_CM 8.0f
```

that bin is considered almost full. This milestone only displays warnings. It does not block sorting based on fullness yet.

Every ultrasonic read uses a timeout:

```c
#define ULTRASONIC_TIMEOUT_US 30000U
```

so missing echo signals cannot block forever.

## TFT Display

The TFT abstraction is isolated in:

```text
Core/Inc/tft_display.h
Core/Src/tft_display.c
```

The placeholder assumes an ILI9341-style SPI TFT may be used, but the exact controller still needs to be confirmed. Until the controller-specific driver is completed, display functions return a clear not-configured/incomplete status instead of pretending to draw text.

Planned display screens:

- Garbage Sorter Ready
- Ready
- Sorting: landfill/compost/recycling
- Done: landfill/compost/recycling
- Error: `<message>`
- Bin-full warnings, including multiple warnings at once

## Supported Commands

```text
PING
STATUS
RESET
SORT class=<class> confidence=<confidence> id=<id>
TEST_DIVERTERS
TEST_TRAPDOOR
TEST_ULTRASONIC
TEST_DISPLAY
```

Valid classes:

```text
landfill
compost
recycling
```

Expected protocol responses:

```text
PONG
STATUS state=IDLE
ACK id=<id>
DONE id=<id>
ERROR id=<id> message=<reason>
```

When hardware is not configured yet, a valid `SORT` returns `ACK` followed by an `ERROR` such as:

```text
ACK id=1
ERROR id=1 message=hardware_not_configured
```

That is intentional. It prevents silent fake success before CubeIDE peripherals and real wiring are ready.

## PuTTY Tests

Open `COM6` at `115200` baud.

Basic protocol:

```text
PING
STATUS
RESET
SORT class=recycling confidence=0.9000 id=1
```

Manual hardware bring-up:

```text
TEST_DIVERTERS
TEST_TRAPDOOR
TEST_ULTRASONIC
TEST_DISPLAY
```

`TEST_ULTRASONIC` reports machine-readable distances as `cm_x100`, for example `cm_x100=1234` means `12.34 cm`.

## Python Diagnostics

From the repo root, with the Python environment activated:

```powershell
python src/hardware_diagnostics.py --check-serial-ping --port COM6
python src/hardware_diagnostics.py --check-serial-sort recycling --port COM6
```

Run serial sort diagnostics only with motors disconnected or while the firmware is still in a safe dry-run/not-configured state.

## Firmware Structure

Custom firmware modules:

```text
Core/Inc/sorter_hardware_config.h
Core/Inc/sorter_types.h
Core/Src/sorter_types.c
Core/Inc/sorter_protocol.h
Core/Src/sorter_protocol.c
Core/Inc/sorter_state.h
Core/Src/sorter_state.c
Core/Inc/servo.h
Core/Src/servo.c
Core/Inc/ultrasonic.h
Core/Src/ultrasonic.c
Core/Inc/tft_display.h
Core/Src/tft_display.c
Core/Inc/sorter_hardware.h
Core/Src/sorter_hardware.c
```

`main.c` remains responsible for HAL startup, blocking UART line receive, dispatching protocol commands, and transmitting protocol responses.
