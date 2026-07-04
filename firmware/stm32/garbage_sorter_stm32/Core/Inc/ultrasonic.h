#ifndef ULTRASONIC_H
#define ULTRASONIC_H

#include "sorter_types.h"

#include <stdint.h>

typedef enum
{
  ULTRASONIC_STATUS_OK = 0,
  ULTRASONIC_STATUS_NOT_CONFIGURED,
  ULTRASONIC_STATUS_TIMEOUT,
  ULTRASONIC_STATUS_INVALID_SENSOR
} UltrasonicStatus;

typedef struct
{
  SorterClass bin_class;
  float distance_cm;
  uint8_t valid;
  UltrasonicStatus status;
} UltrasonicReading;

UltrasonicStatus Ultrasonic_Init(void);
UltrasonicReading Ultrasonic_ReadBin(SorterClass bin_class);
uint8_t Ultrasonic_IsAlmostFull(const UltrasonicReading *reading);
const char *UltrasonicStatus_ToMessage(UltrasonicStatus status);

#endif /* ULTRASONIC_H */
