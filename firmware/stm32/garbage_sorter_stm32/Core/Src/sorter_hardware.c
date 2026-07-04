#include "sorter_hardware.h"
#include "servo.h"
#include "sorter_hardware_config.h"
#include "tft_display.h"

#if SORTER_HARDWARE_ENABLED
#include "stm32f4xx_hal.h"
#endif

#if SORTER_HARDWARE_ENABLED
static SorterHardwareStatus set_route(SorterClass class_name);
static SorterHardwareStatus open_trapdoor(void);
static SorterHardwareStatus close_trapdoor(void);
static SorterHardwareStatus servo_to_hardware_status(ServoStatus status);
static SorterHardwareStatus ultrasonic_to_hardware_status(UltrasonicStatus status);
#endif
static SorterHardwareStatus tft_to_hardware_status(TftStatus status);
static void build_warnings_from_readings(const SorterBinReadings *readings, TftBinWarnings *warnings);

SorterHardwareStatus SorterHardware_Init(void)
{
#if SORTER_HARDWARE_ENABLED
  SorterHardwareStatus status;

  status = servo_to_hardware_status(Servo_InitAll());
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = ultrasonic_to_hardware_status(Ultrasonic_Init());
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = tft_to_hardware_status(TftDisplay_Init());
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = tft_to_hardware_status(TftDisplay_ShowReady());
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  return SORTER_HW_STATUS_OK;
#else
  return SORTER_HW_STATUS_NOT_CONFIGURED;
#endif
}

SorterHardwareStatus SorterHardware_ExecuteSort(SorterClass class_name)
{
#if SORTER_HARDWARE_ENABLED
  SorterHardwareStatus status;

  if (class_name == SORTER_CLASS_UNKNOWN)
  {
    return SORTER_HW_STATUS_INVALID_CLASS;
  }

  (void)TftDisplay_ShowSorting(class_name);

  status = set_route(class_name);
  if (status != SORTER_HW_STATUS_OK)
  {
    (void)TftDisplay_ShowError(SorterHardwareStatus_ToMessage(status));
    return status;
  }

  HAL_Delay(DIVERTER_SETTLE_MS);

  status = open_trapdoor();
  if (status != SORTER_HW_STATUS_OK)
  {
    (void)TftDisplay_ShowError(SorterHardwareStatus_ToMessage(status));
    return status;
  }

  HAL_Delay(TRAPDOOR_OPEN_HOLD_MS);

  status = close_trapdoor();
  if (status != SORTER_HW_STATUS_OK)
  {
    (void)TftDisplay_ShowError(SorterHardwareStatus_ToMessage(status));
    return status;
  }

  HAL_Delay(TRAPDOOR_CLOSE_SETTLE_MS);
  (void)SorterHardware_UpdateBinWarnings();
  (void)TftDisplay_ShowDone(class_name);

  return SORTER_HW_STATUS_OK;
#else
  (void)class_name;
  return SORTER_HW_STATUS_NOT_CONFIGURED;
#endif
}

SorterHardwareStatus SorterHardware_TestDiverters(void)
{
#if SORTER_HARDWARE_ENABLED
  SorterHardwareStatus status;

  status = set_route(SORTER_CLASS_LANDFILL);
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }
  HAL_Delay(DIVERTER_SETTLE_MS);

  status = set_route(SORTER_CLASS_RECYCLING);
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }
  HAL_Delay(DIVERTER_SETTLE_MS);

  status = set_route(SORTER_CLASS_COMPOST);
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }
  HAL_Delay(DIVERTER_SETTLE_MS);

  return SORTER_HW_STATUS_OK;
#else
  return SORTER_HW_STATUS_NOT_CONFIGURED;
#endif
}

SorterHardwareStatus SorterHardware_TestTrapdoor(void)
{
#if SORTER_HARDWARE_ENABLED
  SorterHardwareStatus status;

  status = open_trapdoor();
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  HAL_Delay(TRAPDOOR_OPEN_HOLD_MS);

  status = close_trapdoor();
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  HAL_Delay(TRAPDOOR_CLOSE_SETTLE_MS);
  return SORTER_HW_STATUS_OK;
#else
  return SORTER_HW_STATUS_NOT_CONFIGURED;
#endif
}

SorterHardwareStatus SorterHardware_TestUltrasonic(SorterBinReadings *readings)
{
  if (readings == 0)
  {
    return SORTER_HW_STATUS_ULTRASONIC_ERROR;
  }

  readings->landfill = Ultrasonic_ReadBin(SORTER_CLASS_LANDFILL);
  readings->compost = Ultrasonic_ReadBin(SORTER_CLASS_COMPOST);
  readings->recycling = Ultrasonic_ReadBin(SORTER_CLASS_RECYCLING);

  if (readings->landfill.status == ULTRASONIC_STATUS_NOT_CONFIGURED ||
      readings->compost.status == ULTRASONIC_STATUS_NOT_CONFIGURED ||
      readings->recycling.status == ULTRASONIC_STATUS_NOT_CONFIGURED)
  {
    return SORTER_HW_STATUS_NOT_CONFIGURED;
  }

  if (!readings->landfill.valid || !readings->compost.valid || !readings->recycling.valid)
  {
    return SORTER_HW_STATUS_ULTRASONIC_ERROR;
  }

  return SORTER_HW_STATUS_OK;
}

SorterHardwareStatus SorterHardware_TestDisplay(void)
{
  TftBinWarnings warnings;
  SorterHardwareStatus status;

  status = tft_to_hardware_status(TftDisplay_ShowStartup());
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = tft_to_hardware_status(TftDisplay_ShowReady());
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = tft_to_hardware_status(TftDisplay_ShowSorting(SORTER_CLASS_RECYCLING));
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = tft_to_hardware_status(TftDisplay_ShowDone(SORTER_CLASS_RECYCLING));
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  status = tft_to_hardware_status(TftDisplay_ShowError("test_error"));
  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  warnings.landfill_almost_full = 1;
  warnings.compost_almost_full = 1;
  warnings.recycling_almost_full = 1;
  return tft_to_hardware_status(TftDisplay_ShowBinWarnings(&warnings));
}

SorterHardwareStatus SorterHardware_UpdateBinWarnings(void)
{
  SorterBinReadings readings;
  TftBinWarnings warnings;
  SorterHardwareStatus status = SorterHardware_TestUltrasonic(&readings);

  if (status != SORTER_HW_STATUS_OK)
  {
    return status;
  }

  build_warnings_from_readings(&readings, &warnings);
  return tft_to_hardware_status(TftDisplay_ShowBinWarnings(&warnings));
}

const char *SorterHardwareStatus_ToMessage(SorterHardwareStatus status)
{
  switch (status)
  {
    case SORTER_HW_STATUS_OK:
      return "ok";
    case SORTER_HW_STATUS_NOT_CONFIGURED:
      return "hardware_not_configured";
    case SORTER_HW_STATUS_SERVO_ERROR:
      return "servo_error";
    case SORTER_HW_STATUS_ULTRASONIC_ERROR:
      return "ultrasonic_error";
    case SORTER_HW_STATUS_TFT_ERROR:
      return "tft_error";
    case SORTER_HW_STATUS_INVALID_CLASS:
      return "invalid_class";
    default:
      return "hardware_error";
  }
}

#if SORTER_HARDWARE_ENABLED
static SorterHardwareStatus set_route(SorterClass class_name)
{
  uint32_t diverter_1_us = SERVO_CENTER_PULSE_US;
  uint32_t diverter_2_us = SERVO_CENTER_PULSE_US;
  ServoStatus status;

  switch (class_name)
  {
    case SORTER_CLASS_LANDFILL:
      diverter_1_us = LANDFILL_DIVERTER_1_US;
      diverter_2_us = LANDFILL_DIVERTER_2_US;
      break;
    case SORTER_CLASS_RECYCLING:
      diverter_1_us = RECYCLING_DIVERTER_1_US;
      diverter_2_us = RECYCLING_DIVERTER_2_US;
      break;
    case SORTER_CLASS_COMPOST:
      diverter_1_us = COMPOST_DIVERTER_1_US;
      diverter_2_us = COMPOST_DIVERTER_2_US;
      break;
    case SORTER_CLASS_UNKNOWN:
    default:
      return SORTER_HW_STATUS_INVALID_CLASS;
  }

  status = Servo_SetPulseUs(SERVO_DIVERTER_1, diverter_1_us);
  if (status != SERVO_STATUS_OK)
  {
    return servo_to_hardware_status(status);
  }

  status = Servo_SetPulseUs(SERVO_DIVERTER_2, diverter_2_us);
  return servo_to_hardware_status(status);
}

static SorterHardwareStatus open_trapdoor(void)
{
  ServoStatus left_status;
  ServoStatus right_status;

  left_status = Servo_SetPulseUs(SERVO_TRAPDOOR_LEFT, TRAPDOOR_LEFT_OPEN_US);
  right_status = Servo_SetPulseUs(SERVO_TRAPDOOR_RIGHT, TRAPDOOR_RIGHT_OPEN_US);

  if (left_status != SERVO_STATUS_OK)
  {
    return servo_to_hardware_status(left_status);
  }

  return servo_to_hardware_status(right_status);
}

static SorterHardwareStatus close_trapdoor(void)
{
  ServoStatus left_status;
  ServoStatus right_status;

  left_status = Servo_SetPulseUs(SERVO_TRAPDOOR_LEFT, TRAPDOOR_LEFT_CLOSED_US);
  right_status = Servo_SetPulseUs(SERVO_TRAPDOOR_RIGHT, TRAPDOOR_RIGHT_CLOSED_US);

  if (left_status != SERVO_STATUS_OK)
  {
    return servo_to_hardware_status(left_status);
  }

  return servo_to_hardware_status(right_status);
}

static SorterHardwareStatus servo_to_hardware_status(ServoStatus status)
{
  if (status == SERVO_STATUS_OK)
  {
    return SORTER_HW_STATUS_OK;
  }
  if (status == SERVO_STATUS_NOT_CONFIGURED)
  {
    return SORTER_HW_STATUS_NOT_CONFIGURED;
  }
  return SORTER_HW_STATUS_SERVO_ERROR;
}

static SorterHardwareStatus ultrasonic_to_hardware_status(UltrasonicStatus status)
{
  if (status == ULTRASONIC_STATUS_OK)
  {
    return SORTER_HW_STATUS_OK;
  }
  if (status == ULTRASONIC_STATUS_NOT_CONFIGURED)
  {
    return SORTER_HW_STATUS_NOT_CONFIGURED;
  }
  return SORTER_HW_STATUS_ULTRASONIC_ERROR;
}
#endif

static SorterHardwareStatus tft_to_hardware_status(TftStatus status)
{
  if (status == TFT_STATUS_OK)
  {
    return SORTER_HW_STATUS_OK;
  }
  if (status == TFT_STATUS_NOT_CONFIGURED || status == TFT_STATUS_DRIVER_INCOMPLETE)
  {
    return SORTER_HW_STATUS_NOT_CONFIGURED;
  }
  return SORTER_HW_STATUS_TFT_ERROR;
}

static void build_warnings_from_readings(const SorterBinReadings *readings, TftBinWarnings *warnings)
{
  warnings->landfill_almost_full = Ultrasonic_IsAlmostFull(&readings->landfill);
  warnings->compost_almost_full = Ultrasonic_IsAlmostFull(&readings->compost);
  warnings->recycling_almost_full = Ultrasonic_IsAlmostFull(&readings->recycling);
}
