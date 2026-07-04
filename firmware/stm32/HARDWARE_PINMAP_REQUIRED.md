# Hardware Pin Map Required

The current STM32CubeIDE `.ioc` only configures USART2 and basic NUCLEO board GPIO. Before enabling physical hardware control, update CubeIDE and then edit:

```text
firmware/stm32/garbage_sorter_stm32/Core/Inc/sorter_hardware_config.h
```

Do not scatter pin mappings through the firmware. All manual hardware mapping changes should happen in that config header.

## Required CubeIDE Setup

### Four Servo PWM Outputs

Create PWM channels for:

- Diverter servo 1
- Diverter servo 2
- Trapdoor left servo
- Trapdoor right servo

Recommended timer setup:

- PWM mode
- 50 Hz servo period
- 20,000 us period
- 1 us timer tick

With a 1 us tick:

```text
1000 compare -> 1000 us pulse
1500 compare -> 1500 us pulse
2000 compare -> 2000 us pulse
```

After CubeIDE generates the timer handles, update:

```c
DIVERTER_1_SERVO_TIMER_HANDLE
DIVERTER_1_SERVO_CHANNEL
DIVERTER_2_SERVO_TIMER_HANDLE
DIVERTER_2_SERVO_CHANNEL
TRAPDOOR_LEFT_SERVO_TIMER_HANDLE
TRAPDOOR_LEFT_SERVO_CHANNEL
TRAPDOOR_RIGHT_SERVO_TIMER_HANDLE
TRAPDOOR_RIGHT_SERVO_CHANNEL
SERVO_PWM_TIMER_TICKS_PER_US
```

Current placeholder mappings:

```text
DIVERTER_1_SERVO_TIMER_HANDLE      htim3
DIVERTER_1_SERVO_CHANNEL           TIM_CHANNEL_1
DIVERTER_2_SERVO_TIMER_HANDLE      htim3
DIVERTER_2_SERVO_CHANNEL           TIM_CHANNEL_2
TRAPDOOR_LEFT_SERVO_TIMER_HANDLE   htim4
TRAPDOOR_LEFT_SERVO_CHANNEL        TIM_CHANNEL_1
TRAPDOOR_RIGHT_SERVO_TIMER_HANDLE  htim4
TRAPDOOR_RIGHT_SERVO_CHANNEL       TIM_CHANNEL_2
```

These are placeholders only. They must match the `.ioc` before hardware is enabled.

## Servo Power Warning

Do not power servos from STM32 GPIO or the NUCLEO logic pins.

Use an external servo power supply and connect the supply ground to STM32 ground. Test servos disconnected from the mechanism first.

## Required Ultrasonic GPIO

Create GPIO pins for each ultrasonic sensor:

- Trigger: output
- Echo: input

Sensors:

- Landfill bin fullness sensor
- Compost bin fullness sensor
- Recycling bin fullness sensor

Current placeholder mappings:

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

Create an SPI peripheral for the TFT data bus and GPIO outputs for:

- Chip select
- Data/command
- Reset
- Backlight, if used

Current placeholder mappings:

```text
TFT_SPI_HANDLE  hspi1
TFT_CS_PORT     GPIOA
TFT_CS_PIN      GPIO_PIN_4
TFT_DC_PORT     GPIOA
TFT_DC_PIN      GPIO_PIN_6
TFT_RST_PORT    GPIOA
TFT_RST_PIN     GPIO_PIN_7
TFT_BL_PORT     GPIOA
TFT_BL_PIN      GPIO_PIN_8
```

The display abstraction currently isolates the TFT driver. If the module is ILI9341-compatible, complete the ILI9341 initialization and text drawing inside `tft_display.c`. If it uses another controller, keep the controller-specific code isolated there.

## Enabling Hardware After CubeIDE Setup

After CubeIDE generates the required peripherals and the config header matches your wiring:

```c
#define SORTER_HARDWARE_ENABLED 1
#define SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP 0
```

Then build in STM32CubeIDE.

## Bring-Up Order

Use PuTTY on `COM6` at `115200` baud:

```text
PING
TEST_DIVERTERS
TEST_TRAPDOOR
TEST_ULTRASONIC
TEST_DISPLAY
SORT class=recycling confidence=0.9000 id=1
```

Bring up one subsystem at a time. Keep servos disconnected from the physical mechanism until pulse directions and travel limits are safe.
