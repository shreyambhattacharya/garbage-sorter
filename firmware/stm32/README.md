# STM32 Firmware

This folder contains the STM32CubeIDE firmware project for the garbage sorter dry-run STM32 milestone.

## Hardware

- Board: NUCLEO-F446RE
- IDE: STM32CubeIDE
- UART: USART2
- Baud rate: 115200
- Windows development serial port: COM6

## Current Milestone

The firmware currently implements dry-run serial protocol handling only.

It does not control real motors, servos, actuators, or ultrasonic sensors yet. The purpose of this milestone is to verify reliable Raspberry Pi/Python to STM32 communication before connecting motion hardware.

## Supported Commands

```text
PING
STATUS
RESET
SORT class=<class> confidence=<confidence> id=<id>
```

Valid classes:

```text
landfill
compost
recycling
```

Expected responses:

```text
PONG
STATUS state=IDLE
ACK id=<id>
DONE id=<id>
ERROR id=<id> message=<reason>
```

## PuTTY Tests

Open the board serial port, usually `COM6` during development, at `115200` baud.

Type:

```text
PING
```

Expected:

```text
PONG
```

Type:

```text
STATUS
```

Expected:

```text
STATUS state=IDLE
```

Type:

```text
RESET
```

Expected:

```text
STATUS state=IDLE
```

Type:

```text
SORT class=recycling confidence=0.9000 id=1
```

Expected:

```text
ACK id=1
DONE id=1
```

Type:

```text
SORT class=invalid confidence=0.9000 id=2
```

Expected:

```text
ERROR id=2 message=invalid_class
```

## Python Diagnostics

From the repo root, with the Python environment activated:

```powershell
python src/hardware_diagnostics.py --check-serial-ping --port COM6
python src/hardware_diagnostics.py --check-serial-sort recycling --port COM6
```

Only run the dry sort diagnostic while motors are disconnected or while the STM32 firmware is still in dry-run mode.

## Firmware Structure

The protocol implementation is split out of `main.c`:

```text
Core/Inc/sorter_protocol.h
Core/Src/sorter_protocol.c
Core/Inc/sorter_state.h
Core/Src/sorter_state.c
```

`main.c` is responsible for HAL initialization, reading complete UART lines, passing those lines to the protocol handler, and transmitting response strings.
