# STM32 Integration Plan

The STM32 receives serial commands from the Raspberry Pi/Python side, validates them, controls low-level hardware, and reports success or failure back to the Pi.

This document is the integration plan. The current implemented milestone includes UART protocol handling and four-servo PWM control. Ultrasonic sensors and the TFT display remain planned/in-progress until configured and tested.

## Current Responsibilities

The STM32 currently:

- Receives serial commands over USART2 at `115200` baud.
- Parses `PING`, `STATUS`, `RESET`, and `SORT`.
- Parses manual bring-up commands: `TEST_DIVERTERS`, `TEST_TRAPDOOR`, `TEST_ULTRASONIC`, `TEST_DISPLAY`.
- Sends `ACK id=<id>` quickly after accepting a valid `SORT` command.
- Controls two diverter servos and two trapdoor servos through TIM3 PWM.
- Sends `DONE id=<id>` after the servo sequence succeeds.
- Sends `ERROR id=<id> message=<message>` on validation or hardware failure.

Planned later:

- Read ultrasonic bin fullness sensors.
- Display state and warnings on the SPI TFT.
- Add richer motion fault detection around the mechanical system.

## Current State Machine

```text
IDLE
COMMAND_RECEIVED
SORTING
ERROR
```

Future states may split sorting into more detailed motion states:

```text
ROUTING_DIVERTERS
OPENING_TRAPDOOR
CLOSING_TRAPDOOR
DONE
```

## Command Handling

`PING`:

- Reply with `PONG`.

`STATUS`:

- Reply with `STATUS state=<state>`.

`RESET`:

- Return firmware state to `IDLE`.

`SORT class=<class> confidence=<confidence> id=<id>`:

- Validate class, confidence, and command ID.
- Send `ACK id=<id>`.
- Move diverter servos to the route configured in `sorter_hardware_config.h`.
- Wait for diverters to settle.
- Open both trapdoor servos.
- Hold open.
- Close both trapdoor servos.
- Send `DONE id=<id>` on success.
- Send `ERROR id=<id> message=<reason>` on failure.

`TEST_DIVERTERS`:

- Moves diverter servos through landfill, recycling, and compost routes.
- Returns `DONE test=TEST_DIVERTERS` on success.

`TEST_TRAPDOOR`:

- Opens and closes both trapdoor servos.
- Returns `DONE test=TEST_TRAPDOOR` on success.

`TEST_ULTRASONIC` and `TEST_DISPLAY`:

- Currently return a clear not-configured error until those subsystems are enabled and verified.

## Pseudocode

```c
state = IDLE

loop:
    command = read_serial_line()

    if command == "PING":
        print("PONG")

    else if command == "STATUS":
        print("STATUS state=<current_state>")

    else if command == "RESET":
        state = IDLE
        print("STATUS state=IDLE")

    else if command starts with "SORT":
        parsed = parse_sort_command(command)

        if parsed is invalid:
            print("ERROR id=<id_or_0> message=<reason>")
            continue

        print("ACK id=<command_id>")
        state = SORTING

        if not execute_servo_sort(parsed.class):
            state = ERROR
            print("ERROR id=<command_id> message=servo_error")
            continue

        state = IDLE
        print("DONE id=<command_id>")

    else if command == "TEST_DIVERTERS":
        print("STATUS test=TEST_DIVERTERS result=START")
        run_diverter_test()
        print("DONE test=TEST_DIVERTERS")

    else if command == "TEST_TRAPDOOR":
        print("STATUS test=TEST_TRAPDOOR result=START")
        run_trapdoor_test()
        print("DONE test=TEST_TRAPDOOR")

    else:
        print("ERROR id=0 message=unknown_command")
```

## Failure Handling

The STM32 should fail safe:

- Stop or avoid further motion after a hardware error.
- Reject malformed commands.
- Clamp servo pulse widths.
- Avoid enabling unconfigured ultrasonic/TFT subsystems.
- Report errors with short machine-readable messages.

## Remaining Bring-Up

1. Serial ping.
2. Servo PWM no-load test.
3. `TEST_DIVERTERS` no-load.
4. `TEST_TRAPDOOR` no-load.
5. Mechanical calibration.
6. `SORT` command with servos.
7. Ultrasonic setup.
8. TFT setup.
9. Full closed-loop physical demo.
