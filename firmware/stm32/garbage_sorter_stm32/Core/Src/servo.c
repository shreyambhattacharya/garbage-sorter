#include "servo.h"
#include "sorter_hardware_config.h"

#if SORTER_SERVOS_ACTIVE
#include "stm32f4xx_hal.h"
#endif

#if SORTER_SERVOS_ACTIVE
static uint32_t clamp_pulse_us(uint32_t pulse_us);
#endif

ServoStatus Servo_InitAll(void)
{
#if SORTER_SERVOS_ACTIVE
  if (HAL_TIM_PWM_Start(&DIVERTER_1_SERVO_TIMER_HANDLE, DIVERTER_1_SERVO_CHANNEL) != HAL_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }
  if (HAL_TIM_PWM_Start(&DIVERTER_2_SERVO_TIMER_HANDLE, DIVERTER_2_SERVO_CHANNEL) != HAL_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }
  if (HAL_TIM_PWM_Start(&TRAPDOOR_LEFT_SERVO_TIMER_HANDLE, TRAPDOOR_LEFT_SERVO_CHANNEL) != HAL_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }
  if (HAL_TIM_PWM_Start(&TRAPDOOR_RIGHT_SERVO_TIMER_HANDLE, TRAPDOOR_RIGHT_SERVO_CHANNEL) != HAL_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }

  if (Servo_SetPulseUs(SERVO_DIVERTER_1, SERVO_CENTER_PULSE_US) != SERVO_STATUS_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }
  if (Servo_SetPulseUs(SERVO_DIVERTER_2, SERVO_CENTER_PULSE_US) != SERVO_STATUS_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }
  if (Servo_SetPulseUs(SERVO_TRAPDOOR_LEFT, TRAPDOOR_LEFT_CLOSED_US) != SERVO_STATUS_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }
  if (Servo_SetPulseUs(SERVO_TRAPDOOR_RIGHT, TRAPDOOR_RIGHT_CLOSED_US) != SERVO_STATUS_OK)
  {
    return SERVO_STATUS_HAL_ERROR;
  }

  return SERVO_STATUS_OK;
#else
  return SERVO_STATUS_NOT_CONFIGURED;
#endif
}

ServoStatus Servo_SetPulseUs(ServoId servo, uint32_t pulse_us)
{
#if SORTER_SERVOS_ACTIVE
  uint32_t compare = clamp_pulse_us(pulse_us) * SERVO_PWM_TIMER_TICKS_PER_US;

  switch (servo)
  {
    case SERVO_DIVERTER_1:
      __HAL_TIM_SET_COMPARE(&DIVERTER_1_SERVO_TIMER_HANDLE, DIVERTER_1_SERVO_CHANNEL, compare);
      return SERVO_STATUS_OK;
    case SERVO_DIVERTER_2:
      __HAL_TIM_SET_COMPARE(&DIVERTER_2_SERVO_TIMER_HANDLE, DIVERTER_2_SERVO_CHANNEL, compare);
      return SERVO_STATUS_OK;
    case SERVO_TRAPDOOR_LEFT:
      __HAL_TIM_SET_COMPARE(&TRAPDOOR_LEFT_SERVO_TIMER_HANDLE, TRAPDOOR_LEFT_SERVO_CHANNEL, compare);
      return SERVO_STATUS_OK;
    case SERVO_TRAPDOOR_RIGHT:
      __HAL_TIM_SET_COMPARE(&TRAPDOOR_RIGHT_SERVO_TIMER_HANDLE, TRAPDOOR_RIGHT_SERVO_CHANNEL, compare);
      return SERVO_STATUS_OK;
    default:
      return SERVO_STATUS_INVALID_SERVO;
  }
#else
  (void)servo;
  (void)pulse_us;
  return SERVO_STATUS_NOT_CONFIGURED;
#endif
}

const char *ServoStatus_ToMessage(ServoStatus status)
{
  switch (status)
  {
    case SERVO_STATUS_OK:
      return "ok";
    case SERVO_STATUS_NOT_CONFIGURED:
      return "hardware_not_configured";
    case SERVO_STATUS_HAL_ERROR:
      return "servo_hal_error";
    case SERVO_STATUS_INVALID_SERVO:
      return "invalid_servo";
    default:
      return "servo_error";
  }
}

#if SORTER_SERVOS_ACTIVE
static uint32_t clamp_pulse_us(uint32_t pulse_us)
{
  if (pulse_us < SERVO_MIN_PULSE_US)
  {
    return SERVO_MIN_PULSE_US;
  }

  if (pulse_us > SERVO_MAX_PULSE_US)
  {
    return SERVO_MAX_PULSE_US;
  }

  return pulse_us;
}
#endif
