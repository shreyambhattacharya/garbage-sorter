#ifndef SORTER_HARDWARE_CONFIG_H
#define SORTER_HARDWARE_CONFIG_H

/*
 * Central hardware configuration for the garbage sorter.
 *
 * Current bring-up stage:
 * - Servos: ENABLED
 * - Ultrasonic sensors: DISABLED for now
 * - TFT display: DISABLED for now
 *
 * Servos must be powered from an external 5-6 V supply, not from STM32 GPIO.
 * The external servo supply ground must be connected to STM32 GND.
 */

/* Global hardware architecture switch */
#define SORTER_HARDWARE_ENABLED 1

/* Subsystem-level switches for staged bring-up */
#define SORTER_SERVOS_ENABLED 1
#define SORTER_ULTRASONIC_ENABLED 0
#define SORTER_TFT_ENABLED 0

#define SORTER_SERVOS_ACTIVE (SORTER_HARDWARE_ENABLED && SORTER_SERVOS_ENABLED)
#define SORTER_ULTRASONIC_ACTIVE (SORTER_HARDWARE_ENABLED && SORTER_ULTRASONIC_ENABLED)
#define SORTER_TFT_ACTIVE (SORTER_HARDWARE_ENABLED && SORTER_TFT_ENABLED)

/*
 * CubeIDE setup guard.
 *
 * This is set to 0 because the servo PWM outputs have now been configured.
 * Keep ultrasonic/TFT disabled until those peripherals are configured later.
 */
#define SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP 0

#if SORTER_HARDWARE_ENABLED
#include "main.h"
#endif

#if SORTER_HARDWARE_ENABLED && SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP
#error "Update sorter_hardware_config.h after CubeIDE generates PWM timers, ultrasonic GPIO, and TFT SPI, then set SORTER_HARDWARE_CONFIG_REQUIRES_CUBEIDE_SETUP to 0."
#endif

/*
 * Servo timer/channel mappings.
 *
 * Current servo bring-up assumes all 4 servo PWM outputs are on TIM3:
 *
 * Diverter 1 servo       -> TIM3_CH1
 * Diverter 2 servo       -> TIM3_CH2
 * Trapdoor left servo    -> TIM3_CH3
 * Trapdoor right servo   -> TIM3_CH4
 *
 * Recommended timer setup:
 * - PWM mode
 * - 50 Hz servo period
 * - 1 us timer tick
 * - Counter period = 19999
 * - Pulse = 1500 initially
 */
#if SORTER_SERVOS_ACTIVE
extern TIM_HandleTypeDef htim3;
#endif

#define DIVERTER_1_SERVO_TIMER_HANDLE htim3
#define DIVERTER_1_SERVO_CHANNEL TIM_CHANNEL_1

#define DIVERTER_2_SERVO_TIMER_HANDLE htim3
#define DIVERTER_2_SERVO_CHANNEL TIM_CHANNEL_2

#define TRAPDOOR_LEFT_SERVO_TIMER_HANDLE htim3
#define TRAPDOOR_LEFT_SERVO_CHANNEL TIM_CHANNEL_3

#define TRAPDOOR_RIGHT_SERVO_TIMER_HANDLE htim3
#define TRAPDOOR_RIGHT_SERVO_CHANNEL TIM_CHANNEL_4

/*
 * Ultrasonic pin mappings.
 *
 * Ultrasonic is disabled during servo-only bring-up.
 * These mappings are placeholders for later.
 */
#define LANDFILL_US_TRIG_PORT GPIOB
#define LANDFILL_US_TRIG_PIN GPIO_PIN_0
#define LANDFILL_US_ECHO_PORT GPIOB
#define LANDFILL_US_ECHO_PIN GPIO_PIN_1

#define COMPOST_US_TRIG_PORT GPIOB
#define COMPOST_US_TRIG_PIN GPIO_PIN_2
#define COMPOST_US_ECHO_PORT GPIOB
#define COMPOST_US_ECHO_PIN GPIO_PIN_10

#define RECYCLING_US_TRIG_PORT GPIOB
#define RECYCLING_US_TRIG_PIN GPIO_PIN_11
#define RECYCLING_US_ECHO_PORT GPIOB
#define RECYCLING_US_ECHO_PIN GPIO_PIN_12

/*
 * TFT SPI/control pin mappings.
 *
 * TFT is disabled during servo-only bring-up.
 * These placeholder GPIO definitions exist only so tft_display.c can still compile.
 * Do not connect or test the TFT yet.
 */
#define TFT_CS_PORT GPIOA
#define TFT_CS_PIN GPIO_PIN_4

#define TFT_DC_PORT GPIOA
#define TFT_DC_PIN GPIO_PIN_6

#define TFT_RST_PORT GPIOA
#define TFT_RST_PIN GPIO_PIN_7

#define TFT_BL_PORT GPIOA
#define TFT_BL_PIN GPIO_PIN_8

#define TFT_BACKLIGHT_USED 0

/*
 * Servo calibration values in microseconds.
 *
 * Start conservatively and adjust after the servos are confirmed safe.
 * Do not connect the servos to the physical mechanism until direction and travel
 * limits are verified.
 */
#define SERVO_MIN_PULSE_US 1000U
#define SERVO_CENTER_PULSE_US 1500U
#define SERVO_MAX_PULSE_US 2000U
#define SERVO_PERIOD_US 20000U
#define SERVO_PWM_TIMER_TICKS_PER_US 1U

#define DIVERTER_1_LEFT_US 1000U
#define DIVERTER_1_RIGHT_US 2000U

#define DIVERTER_2_LEFT_US 1000U
#define DIVERTER_2_RIGHT_US 2000U

#define TRAPDOOR_LEFT_CLOSED_US 1000U
#define TRAPDOOR_LEFT_OPEN_US 2000U

#define TRAPDOOR_RIGHT_CLOSED_US 2000U
#define TRAPDOOR_RIGHT_OPEN_US 1000U

#define DIVERTER_SETTLE_MS 600U
#define TRAPDOOR_OPEN_HOLD_MS 900U
#define TRAPDOOR_CLOSE_SETTLE_MS 500U

/*
 * Two-binary-diverter route table.
 *
 * Edit these macros if the physical linkage direction needs to be reversed.
 */
#define LANDFILL_DIVERTER_1_US DIVERTER_1_LEFT_US
#define LANDFILL_DIVERTER_2_US DIVERTER_2_LEFT_US

#define RECYCLING_DIVERTER_1_US DIVERTER_1_RIGHT_US
#define RECYCLING_DIVERTER_2_US DIVERTER_2_LEFT_US

#define COMPOST_DIVERTER_1_US DIVERTER_1_RIGHT_US
#define COMPOST_DIVERTER_2_US DIVERTER_2_RIGHT_US

/*
 * Ultrasonic calibration values.
 *
 * Ultrasonic sensors are disabled during servo-only bring-up.
 */
#define ULTRASONIC_TIMEOUT_US 30000U
#define BIN_ALMOST_FULL_DISTANCE_CM 8.0f

#endif /* SORTER_HARDWARE_CONFIG_H */
