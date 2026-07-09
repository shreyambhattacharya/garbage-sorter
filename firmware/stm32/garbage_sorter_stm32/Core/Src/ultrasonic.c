#include "ultrasonic.h"
#include "sorter_hardware_config.h"

#if SORTER_ULTRASONIC_ACTIVE
#include "stm32f4xx_hal.h"
#endif

typedef struct
{
  SorterClass bin_class;
#if SORTER_ULTRASONIC_ACTIVE
  GPIO_TypeDef *trigger_port;
  uint16_t trigger_pin;
  GPIO_TypeDef *echo_port;
  uint16_t echo_pin;
#endif
} UltrasonicSensorConfig;

static UltrasonicReading make_reading(SorterClass bin_class, float distance_cm, uint8_t valid, UltrasonicStatus status);
#if SORTER_ULTRASONIC_ACTIVE
static const UltrasonicSensorConfig *get_sensor_config(SorterClass bin_class);
static void delay_us(uint32_t delay);
static uint32_t now_us(void);
static uint8_t wait_for_echo(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state, uint32_t timeout_us, uint32_t *timestamp_us);
#endif

UltrasonicStatus Ultrasonic_Init(void)
{
#if SORTER_ULTRASONIC_ACTIVE
  CoreDebug->DEMCR |= CoreDebug_DEMCR_TRCENA_Msk;
  DWT->CYCCNT = 0;
  DWT->CTRL |= DWT_CTRL_CYCCNTENA_Msk;
  return ULTRASONIC_STATUS_OK;
#else
  return ULTRASONIC_STATUS_NOT_CONFIGURED;
#endif
}

UltrasonicReading Ultrasonic_ReadBin(SorterClass bin_class)
{
#if SORTER_ULTRASONIC_ACTIVE
  const UltrasonicSensorConfig *sensor = get_sensor_config(bin_class);
  uint32_t echo_start_us = 0;
  uint32_t echo_end_us = 0;
  uint32_t echo_duration_us = 0;
  float distance_cm = 0.0f;

  if (sensor == 0)
  {
    return make_reading(bin_class, 0.0f, 0, ULTRASONIC_STATUS_INVALID_SENSOR);
  }

  HAL_GPIO_WritePin(sensor->trigger_port, sensor->trigger_pin, GPIO_PIN_RESET);
  delay_us(2);
  HAL_GPIO_WritePin(sensor->trigger_port, sensor->trigger_pin, GPIO_PIN_SET);
  delay_us(10);
  HAL_GPIO_WritePin(sensor->trigger_port, sensor->trigger_pin, GPIO_PIN_RESET);

  if (!wait_for_echo(sensor->echo_port, sensor->echo_pin, GPIO_PIN_SET, ULTRASONIC_TIMEOUT_US, &echo_start_us))
  {
    return make_reading(bin_class, 0.0f, 0, ULTRASONIC_STATUS_TIMEOUT);
  }

  if (!wait_for_echo(sensor->echo_port, sensor->echo_pin, GPIO_PIN_RESET, ULTRASONIC_TIMEOUT_US, &echo_end_us))
  {
    return make_reading(bin_class, 0.0f, 0, ULTRASONIC_STATUS_TIMEOUT);
  }

  echo_duration_us = echo_end_us - echo_start_us;
  distance_cm = ((float)echo_duration_us) / 58.0f;

  return make_reading(bin_class, distance_cm, 1, ULTRASONIC_STATUS_OK);
#else
  return make_reading(bin_class, 0.0f, 0, ULTRASONIC_STATUS_NOT_CONFIGURED);
#endif
}

uint8_t Ultrasonic_IsAlmostFull(const UltrasonicReading *reading)
{
  if (reading == 0 || !reading->valid)
  {
    return 0;
  }

  return reading->distance_cm < BIN_ALMOST_FULL_DISTANCE_CM;
}

const char *UltrasonicStatus_ToMessage(UltrasonicStatus status)
{
  switch (status)
  {
    case ULTRASONIC_STATUS_OK:
      return "ok";
    case ULTRASONIC_STATUS_NOT_CONFIGURED:
      return "hardware_not_configured";
    case ULTRASONIC_STATUS_TIMEOUT:
      return "ultrasonic_timeout";
    case ULTRASONIC_STATUS_INVALID_SENSOR:
      return "invalid_sensor";
    default:
      return "ultrasonic_error";
  }
}

static UltrasonicReading make_reading(SorterClass bin_class, float distance_cm, uint8_t valid, UltrasonicStatus status)
{
  UltrasonicReading reading;
  reading.bin_class = bin_class;
  reading.distance_cm = distance_cm;
  reading.valid = valid;
  reading.status = status;
  return reading;
}

#if SORTER_ULTRASONIC_ACTIVE
static const UltrasonicSensorConfig sensors[] = {
    {SORTER_CLASS_LANDFILL, LANDFILL_US_TRIG_PORT, LANDFILL_US_TRIG_PIN, LANDFILL_US_ECHO_PORT, LANDFILL_US_ECHO_PIN},
    {SORTER_CLASS_COMPOST, COMPOST_US_TRIG_PORT, COMPOST_US_TRIG_PIN, COMPOST_US_ECHO_PORT, COMPOST_US_ECHO_PIN},
    {SORTER_CLASS_RECYCLING, RECYCLING_US_TRIG_PORT, RECYCLING_US_TRIG_PIN, RECYCLING_US_ECHO_PORT, RECYCLING_US_ECHO_PIN},
};

static const UltrasonicSensorConfig *get_sensor_config(SorterClass bin_class)
{
  for (uint32_t i = 0; i < sizeof(sensors) / sizeof(sensors[0]); i++)
  {
    if (sensors[i].bin_class == bin_class)
    {
      return &sensors[i];
    }
  }

  return 0;
}

static void delay_us(uint32_t delay)
{
  uint32_t start = now_us();
  while ((now_us() - start) < delay)
  {
  }
}

static uint32_t now_us(void)
{
  uint32_t ticks_per_us = HAL_RCC_GetHCLKFreq() / 1000000U;
  if (ticks_per_us == 0)
  {
    return 0;
  }

  return DWT->CYCCNT / ticks_per_us;
}

static uint8_t wait_for_echo(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state, uint32_t timeout_us, uint32_t *timestamp_us)
{
  uint32_t start_us = now_us();

  while (HAL_GPIO_ReadPin(port, pin) != state)
  {
    if ((now_us() - start_us) >= timeout_us)
    {
      return 0;
    }
  }

  *timestamp_us = now_us();
  return 1;
}
#endif
