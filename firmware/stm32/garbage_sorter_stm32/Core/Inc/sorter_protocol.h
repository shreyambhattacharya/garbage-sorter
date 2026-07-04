#ifndef SORTER_PROTOCOL_H
#define SORTER_PROTOCOL_H

#include "sorter_types.h"

#include <stdint.h>

#define SORTER_PROTOCOL_MAX_RESPONSE_LINES 8
#define SORTER_PROTOCOL_MAX_RESPONSE_LENGTH 96

typedef enum
{
  SORTER_PROTOCOL_ACTION_RESPOND_ONLY = 0,
  SORTER_PROTOCOL_ACTION_SORT,
  SORTER_PROTOCOL_ACTION_TEST_DIVERTERS,
  SORTER_PROTOCOL_ACTION_TEST_TRAPDOOR,
  SORTER_PROTOCOL_ACTION_TEST_ULTRASONIC,
  SORTER_PROTOCOL_ACTION_TEST_DISPLAY
} SorterProtocolAction;

typedef struct
{
  char lines[SORTER_PROTOCOL_MAX_RESPONSE_LINES][SORTER_PROTOCOL_MAX_RESPONSE_LENGTH];
  uint8_t line_count;
  SorterProtocolAction action;
  SorterClass class_name;
  float confidence;
  int command_id;
} SorterProtocolResult;

void SorterProtocol_Init(void);
void SorterProtocol_HandleLine(const char *line, SorterProtocolResult *result);

#endif /* SORTER_PROTOCOL_H */
