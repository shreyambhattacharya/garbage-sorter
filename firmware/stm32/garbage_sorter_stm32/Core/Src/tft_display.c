#include "tft_display.h"
#include "sorter_hardware_config.h"

#if SORTER_TFT_ACTIVE
#include "stm32f4xx_hal.h"
#endif

/*
 * Placeholder SPI TFT abstraction.
 *
 * The planned display is a 2.4-inch SPI TFT. Many modules use an ILI9341
 * controller, but the exact controller should be verified before writing the
 * final pixel/text driver. This file intentionally isolates that future driver.
 */

TftStatus TftDisplay_Init(void)
{
#if SORTER_TFT_ACTIVE
  HAL_GPIO_WritePin(TFT_CS_PORT, TFT_CS_PIN, GPIO_PIN_SET);
  HAL_GPIO_WritePin(TFT_RST_PORT, TFT_RST_PIN, GPIO_PIN_RESET);
  HAL_Delay(20);
  HAL_GPIO_WritePin(TFT_RST_PORT, TFT_RST_PIN, GPIO_PIN_SET);
  HAL_Delay(120);
#if TFT_BACKLIGHT_USED
  HAL_GPIO_WritePin(TFT_BL_PORT, TFT_BL_PIN, GPIO_PIN_SET);
#endif
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

TftStatus TftDisplay_ShowStartup(void)
{
#if SORTER_TFT_ACTIVE
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

TftStatus TftDisplay_ShowReady(void)
{
#if SORTER_TFT_ACTIVE
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

TftStatus TftDisplay_ShowSorting(SorterClass class_name)
{
  (void)class_name;
#if SORTER_TFT_ACTIVE
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

TftStatus TftDisplay_ShowDone(SorterClass class_name)
{
  (void)class_name;
#if SORTER_TFT_ACTIVE
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

TftStatus TftDisplay_ShowError(const char *message)
{
  (void)message;
#if SORTER_TFT_ACTIVE
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

TftStatus TftDisplay_ShowBinWarnings(const TftBinWarnings *warnings)
{
  (void)warnings;
#if SORTER_TFT_ACTIVE
  return TFT_STATUS_DRIVER_INCOMPLETE;
#else
  return TFT_STATUS_NOT_CONFIGURED;
#endif
}

const char *TftStatus_ToMessage(TftStatus status)
{
  switch (status)
  {
    case TFT_STATUS_OK:
      return "ok";
    case TFT_STATUS_NOT_CONFIGURED:
      return "hardware_not_configured";
    case TFT_STATUS_DRIVER_INCOMPLETE:
      return "tft_driver_incomplete";
    default:
      return "tft_error";
  }
}
