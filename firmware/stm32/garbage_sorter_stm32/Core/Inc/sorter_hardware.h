#ifndef SORTER_HARDWARE_H
#define SORTER_HARDWARE_H

#include "sorter_types.h"
#include "ultrasonic.h"

#include <stdint.h>

typedef enum
{
  SORTER_HW_STATUS_OK = 0,
  SORTER_HW_STATUS_NOT_CONFIGURED,
  SORTER_HW_STATUS_SERVO_ERROR,
  SORTER_HW_STATUS_ULTRASONIC_ERROR,
  SORTER_HW_STATUS_TFT_ERROR,
  SORTER_HW_STATUS_INVALID_CLASS
} SorterHardwareStatus;

typedef struct
{
  UltrasonicReading landfill;
  UltrasonicReading compost;
  UltrasonicReading recycling;
} SorterBinReadings;

SorterHardwareStatus SorterHardware_Init(void);
SorterHardwareStatus SorterHardware_ExecuteSort(SorterClass class_name);
SorterHardwareStatus SorterHardware_TestDiverters(void);
SorterHardwareStatus SorterHardware_TestTrapdoor(void);
SorterHardwareStatus SorterHardware_TestUltrasonic(SorterBinReadings *readings);
SorterHardwareStatus SorterHardware_TestDisplay(void);
SorterHardwareStatus SorterHardware_UpdateBinWarnings(void);
const char *SorterHardwareStatus_ToMessage(SorterHardwareStatus status);

#endif /* SORTER_HARDWARE_H */
