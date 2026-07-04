#ifndef TFT_DISPLAY_H
#define TFT_DISPLAY_H

#include "sorter_types.h"

#include <stdint.h>

typedef enum
{
  TFT_STATUS_OK = 0,
  TFT_STATUS_NOT_CONFIGURED,
  TFT_STATUS_DRIVER_INCOMPLETE
} TftStatus;

typedef struct
{
  uint8_t landfill_almost_full;
  uint8_t compost_almost_full;
  uint8_t recycling_almost_full;
} TftBinWarnings;

TftStatus TftDisplay_Init(void);
TftStatus TftDisplay_ShowStartup(void);
TftStatus TftDisplay_ShowReady(void);
TftStatus TftDisplay_ShowSorting(SorterClass class_name);
TftStatus TftDisplay_ShowDone(SorterClass class_name);
TftStatus TftDisplay_ShowError(const char *message);
TftStatus TftDisplay_ShowBinWarnings(const TftBinWarnings *warnings);
const char *TftStatus_ToMessage(TftStatus status);

#endif /* TFT_DISPLAY_H */
