# Hardware Pin Map Required

This file tracks hardware pin/peripheral setup for the STM32CubeIDE project.

Current verified milestone:

- USART2 serial communication works on `COM6`.
- TIM3 PWM is configured for four servos.
- Diverter and trapdoor servo tests work locally.

Remaining future work:

- Ultrasonic GPIO setup.
- SPI TFT setup and controller-specific display driver.

All manual hardware mappings should remain centralized in:

```text
firmware/stm32/garbage_sorter_stm32/Core/Inc/sorter_hardware_config.h
```

## Current Servo PWM Setup

Configured in CubeIDE:

```text
Diverter servo 1       PA6  -> TIM3_CH1
Diverter servo 2       PA7  -> TIM3_CH2
Trapdoor left servo    PB0  -> TIM3_CH3
Trapdoor right servo   PB1  -> TIM3_CH4
```

TIM3 configuration:

```text
Prescaler: 83
Period: 19999
Initial pulse: 1500
```

With the current timer clock, this gives:

```text
1000 compare -> 1000 us pulse
1500 compare -> 1500 us pulse
2000 compare -> 2000 us pulse
```

Current config macros:

```c
#define SORTER_HARDWARE_ENABLED 1
#define SORTER_SERVOS_ENABLED 1
#define SORTER_ULTRASONIC_ENABLED 0
#define SORTER_TFT_ENABLED 0
```

Current servo mappings:

```text
DIVERTER_1_SERVO_TIMER_HANDLE      htim3
DIVERTER_1_SERVO_CHANNEL           TIM_CHANNEL_1
DIVERTER_2_SERVO_TIMER_HANDLE      htim3
DIVERTER_2_SERVO_CHANNEL           TIM_CHANNEL_2
TRAPDOOR_LEFT_SERVO_TIMER_HANDLE   htim3
TRAPDOOR_LEFT_SERVO_CHANNEL        TIM_CHANNEL_3
TRAPDOOR_RIGHT_SERVO_TIMER_HANDLE  htim3
TRAPDOOR_RIGHT_SERVO_CHANNEL       TIM_CHANNEL_4
```

## Servo Power Warning

Do not power servos from STM32 GPIO or the NUCLEO logic pins.

Use an external 5-6 V servo power supply and connect the external supply ground to STM32 ground. Test servos disconnected from the mechanism first.

## Servo Calibration

Tune these in `sorter_hardware_config.h`:

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

Start conservatively. If a servo direction is reversed mechanically, update the route/calibration macros rather than changing motion code.

## Required Ultrasonic GPIO Setup

Ultrasonic sensors are currently disabled:

```c
#define SORTER_ULTRASONIC_ENABLED 0
```

Before enabling them, create GPIO pins for each sensor:

- Trigger: output
- Echo: input

Sensors:

- Landfill bin fullness sensor
- Compost bin fullness sensor
- Recycling bin fullness sensor

Placeholder mappings in the config header:

```text
LANDFILL_US_TRIG_PORT     GPIOB
LANDFILL_US_TRIG_PIN      GPIO_PIN_0
LANDFILL_US_ECHO_PORT     GPIOB
LANDFILL_US_ECHO_PIN      GPIO_PIN_1

COMPOST_US_TRIG_PORT      GPIOB
COMPOST_US_TRIG_PIN       GPIO_PIN_2
COMPOST_US_ECHO_PORT      GPIOB
COMPOST_US_ECHO_PIN       GPIO_PIN_10

RECYCLING_US_TRIG_PORT    GPIOB
RECYCLING_US_TRIG_PIN     GPIO_PIN_11
RECYCLING_US_ECHO_PORT    GPIOB
RECYCLING_US_ECHO_PIN     GPIO_PIN_12
```

These are placeholders only. Confirm voltage compatibility for ultrasonic echo pins before wiring.

## Required SPI/TFT Setup

The TFT display is currently disabled:

```c
#define SORTER_TFT_ENABLED 0
```

Before enabling it, configure:

- SPI peripheral
- Chip select GPIO
- Data/command GPIO
- Reset GPIO
- Backlight GPIO, if used

Placeholder mappings in the config header:

```text
TFT_CS_PORT     GPIOA
TFT_CS_PIN      GPIO_PIN_4
TFT_DC_PORT     GPIOA
TFT_DC_PIN      GPIO_PIN_6
TFT_RST_PORT    GPIOA
TFT_RST_PIN     GPIO_PIN_7
TFT_BL_PORT     GPIOA
TFT_BL_PIN      GPIO_PIN_8
```

The display abstraction currently isolates the TFT driver. Confirm the exact controller before implementing the final driver. If the module is ILI9341-compatible, keep the ILI9341-specific initialization inside `tft_display.c`.

## Bring-Up Commands

Use PuTTY on `COM6` at `115200` baud:

```text
PING
TEST_DIVERTERS
TEST_TRAPDOOR
SORT class=recycling confidence=0.9000 id=1
TEST_ULTRASONIC
TEST_DISPLAY
```

Expected current state:

- `TEST_DIVERTERS` should move servos and return `DONE test=TEST_DIVERTERS`.
- `TEST_TRAPDOOR` should move servos and return `DONE test=TEST_TRAPDOOR`.
- `TEST_ULTRASONIC` should return `hardware_not_configured`.
- `TEST_DISPLAY` should return `hardware_not_configured`.
