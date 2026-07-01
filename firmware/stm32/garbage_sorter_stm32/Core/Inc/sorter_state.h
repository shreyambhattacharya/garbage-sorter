#ifndef SORTER_STATE_H
#define SORTER_STATE_H

typedef enum
{
  SORTER_STATE_IDLE = 0,
  SORTER_STATE_COMMAND_RECEIVED,
  SORTER_STATE_SORTING,
  SORTER_STATE_ERROR
} SorterState;

void SorterState_Init(void);
void SorterState_Reset(void);
void SorterState_Set(SorterState state);
SorterState SorterState_Get(void);
const char *SorterState_ToString(SorterState state);

#endif /* SORTER_STATE_H */
