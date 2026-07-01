# STM32 Integration Plan

The STM32 receives serial commands from the Raspberry Pi, controls the sorting mechanism, reads sensors, and reports success or failure back to the Pi.

This document is a plan, not full firmware.

## Responsibilities

The STM32 should:

- Receive serial commands from the Pi.
- Parse `PING`, `SORT`, `STATUS`, and `RESET`.
- Send `ACK id=<id>` quickly after accepting a `SORT` command.
- Control the chute motor.
- Control the trapdoor actuator.
- Read ultrasonic sensors.
- Enforce motion timeouts.
- Send `DONE id=<id>` on success.
- Send `ERROR id=<id> message=<message>` on failure.

## Suggested State Machine

```text
IDLE
COMMAND_RECEIVED
ROTATING_CHUTE
OPENING_TRAPDOOR
CLOSING_TRAPDOOR
RETURNING_HOME
DONE
ERROR
```

## Command Handling

`PING`:

- Reply with `PONG`.

`STATUS`:

- Reply with `STATUS state=<state>`.

`RESET`:

- Stop motion.
- Return outputs to a safe state.
- Attempt to return to `IDLE`.

`SORT class=<class> confidence=<confidence> id=<id>`:

- Validate class.
- Store command ID.
- Send `ACK id=<id>`.
- Rotate chute to the requested bin.
- Open trapdoor.
- Close trapdoor.
- Return mechanism home if needed.
- Send `DONE id=<id>`.

## Pseudocode

```c
state = IDLE

loop:
    if serial_line_available:
        command = read_line()

        if command == "PING":
            print("PONG")

        else if command == "STATUS":
            print("STATUS state=<current_state>")

        else if command == "RESET":
            stop_all_motion()
            return_outputs_to_safe_state()
            state = IDLE

        else if command starts with "SORT":
            parsed = parse_sort_command(command)

            if parsed is invalid:
                print("ERROR id=0 message=invalid_command")
                continue

            command_id = parsed.id
            target_class = parsed.class
            print("ACK id=<command_id>")

            state = COMMAND_RECEIVED

            if not rotate_chute_to_bin(target_class, timeout_ms):
                state = ERROR
                print("ERROR id=<command_id> message=chute_timeout")
                continue

            state = OPENING_TRAPDOOR
            if not open_trapdoor(timeout_ms):
                state = ERROR
                print("ERROR id=<command_id> message=trapdoor_open_timeout")
                continue

            state = CLOSING_TRAPDOOR
            if not close_trapdoor(timeout_ms):
                state = ERROR
                print("ERROR id=<command_id> message=trapdoor_close_timeout")
                continue

            state = RETURNING_HOME
            if not return_home_if_needed(timeout_ms):
                state = ERROR
                print("ERROR id=<command_id> message=home_timeout")
                continue

            state = DONE
            print("DONE id=<command_id>")
            state = IDLE

        else:
            print("ERROR id=0 message=unknown_command")
```

## Failure Handling

The STM32 should fail safe:

- Stop motion on timeout.
- Stop motion on sensor disagreement.
- Stop motion on malformed commands.
- Avoid repeated actuator motion after an error until reset or a known-safe state is reached.
- Report errors with a short machine-readable message.

## Hardware Bringup Order

1. Serial parser only.
2. Chute motor disconnected from mechanism.
3. Trapdoor actuator disconnected from mechanism.
4. Ultrasonic sensors alone.
5. Mechanism attached with no items.
6. One item at a time.
7. Full integrated test.
