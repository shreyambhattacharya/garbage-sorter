#ifndef SORTER_PROTOCOL_H
#define SORTER_PROTOCOL_H

#include <stdint.h>

#define SORTER_PROTOCOL_MAX_RESPONSE_LINES 3
#define SORTER_PROTOCOL_MAX_RESPONSE_LENGTH 96

typedef struct
{
  char lines[SORTER_PROTOCOL_MAX_RESPONSE_LINES][SORTER_PROTOCOL_MAX_RESPONSE_LENGTH];
  uint8_t line_count;
  uint8_t accepted_sort;
} SorterProtocolResponse;

void SorterProtocol_Init(void);
void SorterProtocol_HandleLine(const char *line, SorterProtocolResponse *response);

#endif /* SORTER_PROTOCOL_H */
