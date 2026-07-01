# Serial Protocol

The Raspberry Pi and STM32 communicate with newline-terminated ASCII text lines.

## Serial Settings

- Baud rate: `115200`
- Encoding: ASCII-compatible text
- Line ending: newline, `\n`

## Pi To STM32 Commands

```text
PING
SORT class=<class> confidence=<confidence> id=<id>
STATUS
RESET
```

Valid classes:

```text
landfill
compost
recycling
```

## STM32 Responses

```text
PONG
ACK id=<id>
DONE id=<id>
ERROR id=<id> message=<message>
STATUS state=<state>
```

## Command IDs

`SORT` commands include an integer command ID. The STM32 should include the same ID in `ACK`, `DONE`, and `ERROR` responses so the Pi can match responses to the command that triggered them.

Example:

```text
Pi:    SORT class=recycling confidence=0.9200 id=7
STM32: ACK id=7
STM32: DONE id=7
```

## Timeout Behavior

The Pi expects:

- `PING` -> `PONG` before the serial timeout expires.
- `SORT` -> `ACK id=<id>` before the short serial timeout expires.
- `SORT` -> `DONE id=<id>` before the longer sort timeout expires.
- `SORT` -> `ERROR id=<id> message=<message>` if the STM32 cannot complete the command.

If the Pi receives malformed lines, it should report them and continue waiting until the expected response or timeout.

If the STM32 cannot parse a command, it should send an `ERROR` response when possible.

## Example: Ping

```text
Pi:    PING
STM32: PONG
```

## Example: Status

```text
Pi:    STATUS
STM32: STATUS state=IDLE
```

## Example: Successful Sort

```text
Pi:    SORT class=compost confidence=0.8734 id=12
STM32: ACK id=12
STM32: DONE id=12
```

## Example: Failed Sort

```text
Pi:    SORT class=landfill confidence=0.9132 id=13
STM32: ACK id=13
STM32: ERROR id=13 message=chute_timeout
```

## Example: Reset

```text
Pi:    RESET
STM32: STATUS state=IDLE
```
