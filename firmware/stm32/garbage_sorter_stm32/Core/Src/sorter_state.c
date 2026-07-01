#include "sorter_state.h"

static SorterState current_state = SORTER_STATE_IDLE;

void SorterState_Init(void)
{
  current_state = SORTER_STATE_IDLE;
}

void SorterState_Reset(void)
{
  current_state = SORTER_STATE_IDLE;
}

void SorterState_Set(SorterState state)
{
  current_state = state;
}

SorterState SorterState_Get(void)
{
  return current_state;
}

const char *SorterState_ToString(SorterState state)
{
  switch (state)
  {
    case SORTER_STATE_IDLE:
      return "IDLE";
    case SORTER_STATE_COMMAND_RECEIVED:
      return "COMMAND_RECEIVED";
    case SORTER_STATE_SORTING:
      return "SORTING";
    case SORTER_STATE_ERROR:
      return "ERROR";
    default:
      return "ERROR";
  }
}
