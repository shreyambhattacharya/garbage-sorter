#include "sorter_protocol.h"
#include "sorter_state.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SORTER_COMMAND_BUFFER_LENGTH 128

static void clear_result(SorterProtocolResult *result);
static void add_response_line(SorterProtocolResult *result, const char *format, ...);
static void handle_sort_command(const char *line, SorterProtocolResult *result);
static int parse_positive_int(const char *text, int *value);
static int parse_confidence(const char *text, float *value);

void SorterProtocol_Init(void)
{
  SorterState_Init();
}

void SorterProtocol_HandleLine(const char *line, SorterProtocolResult *result)
{
  clear_result(result);

  if (strcmp(line, "PING") == 0)
  {
    add_response_line(result, "PONG");
    return;
  }

  if (strcmp(line, "STATUS") == 0)
  {
    add_response_line(result, "STATUS state=%s", SorterState_ToString(SorterState_Get()));
    return;
  }

  if (strcmp(line, "RESET") == 0)
  {
    SorterState_Reset();
    add_response_line(result, "STATUS state=IDLE");
    return;
  }

  if (strncmp(line, "SORT", 4) == 0 && (line[4] == '\0' || line[4] == ' '))
  {
    handle_sort_command(line, result);
    return;
  }

  if (strcmp(line, "TEST_DIVERTERS") == 0)
  {
    result->action = SORTER_PROTOCOL_ACTION_TEST_DIVERTERS;
    return;
  }

  if (strcmp(line, "TEST_TRAPDOOR") == 0)
  {
    result->action = SORTER_PROTOCOL_ACTION_TEST_TRAPDOOR;
    return;
  }

  if (strcmp(line, "TEST_ULTRASONIC") == 0)
  {
    result->action = SORTER_PROTOCOL_ACTION_TEST_ULTRASONIC;
    return;
  }

  if (strcmp(line, "TEST_DISPLAY") == 0)
  {
    result->action = SORTER_PROTOCOL_ACTION_TEST_DISPLAY;
    return;
  }

  SorterState_Set(SORTER_STATE_ERROR);
  add_response_line(result, "ERROR id=0 message=unknown_command");
}

static void clear_result(SorterProtocolResult *result)
{
  result->line_count = 0;
  result->action = SORTER_PROTOCOL_ACTION_RESPOND_ONLY;
  result->class_name = SORTER_CLASS_UNKNOWN;
  result->confidence = 0.0f;
  result->command_id = 0;
  for (uint8_t i = 0; i < SORTER_PROTOCOL_MAX_RESPONSE_LINES; i++)
  {
    result->lines[i][0] = '\0';
  }
}

static void add_response_line(SorterProtocolResult *result, const char *format, ...)
{
  if (result->line_count >= SORTER_PROTOCOL_MAX_RESPONSE_LINES)
  {
    return;
  }

  va_list args;
  va_start(args, format);
  vsnprintf(
      result->lines[result->line_count],
      SORTER_PROTOCOL_MAX_RESPONSE_LENGTH,
      format,
      args);
  va_end(args);

  result->line_count++;
}

static void handle_sort_command(const char *line, SorterProtocolResult *result)
{
  char command_copy[SORTER_COMMAND_BUFFER_LENGTH];
  char *class_value = NULL;
  char *confidence_value = NULL;
  char *id_value = NULL;
  int command_id = 0;
  float confidence = 0.0f;
  SorterClass parsed_class = SORTER_CLASS_UNKNOWN;

  strncpy(command_copy, line, sizeof(command_copy) - 1);
  command_copy[sizeof(command_copy) - 1] = '\0';

  char *token = strtok(command_copy, " ");
  while (token != NULL)
  {
    if (strncmp(token, "class=", 6) == 0)
    {
      class_value = token + 6;
    }
    else if (strncmp(token, "confidence=", 11) == 0)
    {
      confidence_value = token + 11;
    }
    else if (strncmp(token, "id=", 3) == 0)
    {
      id_value = token + 3;
    }

    token = strtok(NULL, " ");
  }

  if (id_value == NULL)
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(result, "ERROR id=0 message=missing_id");
    return;
  }

  if (!parse_positive_int(id_value, &command_id))
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(result, "ERROR id=0 message=invalid_id");
    return;
  }

  if (class_value == NULL)
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(result, "ERROR id=%d message=missing_class", command_id);
    return;
  }

  if (confidence_value == NULL)
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(result, "ERROR id=%d message=missing_confidence", command_id);
    return;
  }

  parsed_class = SorterClass_FromString(class_value);
  if (parsed_class == SORTER_CLASS_UNKNOWN)
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(result, "ERROR id=%d message=invalid_class", command_id);
    return;
  }

  if (!parse_confidence(confidence_value, &confidence))
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(result, "ERROR id=%d message=invalid_confidence", command_id);
    return;
  }

  result->action = SORTER_PROTOCOL_ACTION_SORT;
  result->class_name = parsed_class;
  result->confidence = confidence;
  result->command_id = command_id;
}

static int parse_positive_int(const char *text, int *value)
{
  char *end_ptr = NULL;
  long parsed = strtol(text, &end_ptr, 10);

  if (text[0] == '\0' || end_ptr == text || *end_ptr != '\0' || parsed <= 0)
  {
    return 0;
  }

  *value = (int)parsed;
  return 1;
}

static int parse_confidence(const char *text, float *value)
{
  char *end_ptr = NULL;
  float parsed = strtof(text, &end_ptr);

  if (text[0] == '\0' || end_ptr == text || *end_ptr != '\0')
  {
    return 0;
  }

  if (parsed < 0.0f || parsed > 1.0f)
  {
    return 0;
  }

  *value = parsed;
  return 1;
}
