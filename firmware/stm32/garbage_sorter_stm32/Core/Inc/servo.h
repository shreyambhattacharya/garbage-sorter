#ifndef SERVO_H
#define SERVO_H

#include <stdint.h>

typedef enum
{
  SERVO_DIVERTER_1 = 0,
  SERVO_DIVERTER_2,
  SERVO_TRAPDOOR_LEFT,
  SERVO_TRAPDOOR_RIGHT
} ServoId;

typedef enum
{
  SERVO_STATUS_OK = 0,
  SERVO_STATUS_NOT_CONFIGURED,
  SERVO_STATUS_HAL_ERROR,
  SERVO_STATUS_INVALID_SERVO
} ServoStatus;

ServoStatus Servo_InitAll(void);
ServoStatus Servo_SetPulseUs(ServoId servo, uint32_t pulse_us);
const char *ServoStatus_ToMessage(ServoStatus status);

#endif /* SERVO_H */
