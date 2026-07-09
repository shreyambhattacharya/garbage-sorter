# STM32 Firmware

This folder contains the STM32CubeIDE firmware project for the Garbage Sorter STM32 side.

The current firmware supports the serial command protocol plus a servo-control milestone for the garbage sorter mechanism. It is not a completed full physical sorter yet: ultrasonic bin sensors and the SPI TFT display are scaffolded but disabled until those peripherals are configured and tested.

## Hardware

- Board: NUCLEO-F446RE
- IDE: STM32CubeIDE
- UART: USART2
- Baud rate: `115200`
- Windows development serial port: `COM6`
- Servo PWM timer: `TIM3`
- Servo PWM channels: `TIM3_CH1`, `TIM3_CH2`, `TIM3_CH3`, `TIM3_CH4`

## Current Firmware State

Implemented and locally verified:

- `PING`, `STATUS`, `RESET`, and `SORT` command parsing
- `ACK` / `DONE` / `ERROR` protocol responses
- State tracking
- Four-servo PWM bring-up using TIM3
- `TEST_DIVERTERS`
- `TEST_TRAPDOOR`

Scaffolded but not yet verified:

- Ultrasonic bin fullness sensors
- SPI TFT status display

## Subsystem Flags

Hardware bring-up is controlled from:

```text
Core/Inc/sorter_hardware_config.h
```

Current intended flags:

```c
#define SORTER_HARDWARE_ENABLED 1
#define SORTER_SERVOS_ENABLED 1
#define SORTER_ULTRASONIC_ENABLED 0
#define SORTER_TFT_ENABLED 0
#define SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP 0
```

This means the STM32 firmware can run servo tests and serial sorts, while ultrasonic and TFT code return clear not-configured responses instead of touching placeholder pins.

## Servo Configuration

Current PWM mapping:

```text
Diverter 1 servo       -> TIM3_CH1
Diverter 2 servo       -> TIM3_CH2
Trapdoor left servo    -> TIM3_CH3
Trapdoor right servo   -> TIM3_CH4
```

TIM3 is configured for a servo-style PWM period:

```text
Prescaler: 83
Period: 19999
Initial pulse: 1500
```

With the current 84 MHz timer clock, this gives a 1 us timer tick and a 20 ms servo period.

Servo calibration values are editable in `sorter_hardware_config.h`:

```c
SERVO_MIN_PULSE_US
SERVO_CENTER_PULSE_US
SERVO_MAX_PULSE_US
DIVERTER_1_LEFT_US
DIVERTER_1_RIGHT_US
DIVERTER_2_LEFT_US
DIVERTER_2_RIGHT_US
TRAPDOOR_LEFT_CLOSED_US
TRAPDOOR_LEFT_OPEN_US
TRAPDOOR_RIGHT_CLOSED_US
TRAPDOOR_RIGHT_OPEN_US
```

Start conservatively. Do not attach servos to the physical mechanism until direction, pulse ranges, and travel limits are safe.

## Safety

- Do not power servos from STM32 GPIO.
- Use an external 5-6 V servo supply.
- Connect the external servo supply ground to STM32 ground.
- Run `TEST_DIVERTERS` and `TEST_TRAPDOOR` no-load before attaching linkages.
- Keep pulse widths configurable and conservative.

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

Expected examples:

```text
PING
PONG

STATUS
STATUS state=IDLE

TEST_DIVERTERS
STATUS test=TEST_DIVERTERS result=START
DONE test=TEST_DIVERTERS

TEST_TRAPDOOR
STATUS test=TEST_TRAPDOOR result=START
DONE test=TEST_TRAPDOOR

TEST_ULTRASONIC
STATUS test=TEST_ULTRASONIC result=START
ERROR id=0 message=hardware_not_configured

TEST_DISPLAY
STATUS test=TEST_DISPLAY result=START
ERROR id=0 message=hardware_not_configured

SORT class=recycling confidence=0.9000 id=1
ACK id=1
DONE id=1
```

`TEST_ULTRASONIC` and `TEST_DISPLAY` should fail cleanly until those subsystems are enabled and tested.

## PuTTY Bring-Up

Open `COM6` at `115200` baud.

Recommended sequence:

```text
PING
STATUS
TEST_DIVERTERS
TEST_TRAPDOOR
SORT class=recycling confidence=0.9000 id=1
TEST_ULTRASONIC
TEST_DISPLAY
```

Run the servo commands no-load first. Physical sorting reliability depends on mechanism geometry, object placement, and calibration.

## Python Diagnostics

From the repo root, with the Python environment activated:

```powershell
python src/hardware_diagnostics.py --check-serial-ping --port COM6
python src/hardware_diagnostics.py --test-diverters --port COM6
python src/hardware_diagnostics.py --test-trapdoor --port COM6
python src/hardware_diagnostics.py --check-serial-sort recycling --port COM6
python src/hardware_diagnostics.py --test-ultrasonic --port COM6
python src/hardware_diagnostics.py --test-display --port COM6
```

## Future Pin Map Work

Keep future ultrasonic/TFT setup notes here:

```text
firmware/stm32/HARDWARE_PINMAP_REQUIRED.md
```

That file lists the remaining CubeIDE GPIO/SPI setup and placeholder mappings.

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
