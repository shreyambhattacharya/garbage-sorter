#include "sorter_protocol.h"
#include "sorter_state.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define SORTER_COMMAND_BUFFER_LENGTH 128

static void clear_response(SorterProtocolResponse *response);
static void add_response_line(SorterProtocolResponse *response, const char *format, ...);
static void handle_sort_command(const char *line, SorterProtocolResponse *response);
static int is_valid_class(const char *class_name);
static int parse_positive_int(const char *text, int *value);
static int parse_confidence(const char *text, float *value);

void SorterProtocol_Init(void)
{
  SorterState_Init();
}

void SorterProtocol_HandleLine(const char *line, SorterProtocolResponse *response)
{
  clear_response(response);

  if (strcmp(line, "PING") == 0)
  {
    add_response_line(response, "PONG");
    return;
  }

  if (strcmp(line, "STATUS") == 0)
  {
    add_response_line(response, "STATUS state=%s", SorterState_ToString(SorterState_Get()));
    return;
  }

  if (strcmp(line, "RESET") == 0)
  {
    SorterState_Reset();
    add_response_line(response, "STATUS state=IDLE");
    return;
  }

  if (strncmp(line, "SORT", 4) == 0 && (line[4] == '\0' || line[4] == ' '))
  {
    handle_sort_command(line, response);
    return;
  }

  SorterState_Set(SORTER_STATE_ERROR);
  add_response_line(response, "ERROR id=0 message=unknown_command");
}

static void clear_response(SorterProtocolResponse *response)
{
  response->line_count = 0;
  response->accepted_sort = 0;
  for (uint8_t i = 0; i < SORTER_PROTOCOL_MAX_RESPONSE_LINES; i++)
  {
    response->lines[i][0] = '\0';
  }
}

static void add_response_line(SorterProtocolResponse *response, const char *format, ...)
{
  if (response->line_count >= SORTER_PROTOCOL_MAX_RESPONSE_LINES)
  {
    return;
  }

  va_list args;
  va_start(args, format);
  vsnprintf(
      response->lines[response->line_count],
      SORTER_PROTOCOL_MAX_RESPONSE_LENGTH,
      format,
      args);
  va_end(args);

  response->line_count++;
}

static void handle_sort_command(const char *line, SorterProtocolResponse *response)
{
  char command_copy[SORTER_COMMAND_BUFFER_LENGTH];
  char *class_value = NULL;
  char *confidence_value = NULL;
  char *id_value = NULL;
  int command_id = 0;
  float confidence = 0.0f;

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
    add_response_line(response, "ERROR id=0 message=missing_id");
    return;
  }

  if (!parse_positive_int(id_value, &command_id))
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(response, "ERROR id=0 message=invalid_id");
    return;
  }

  if (class_value == NULL)
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(response, "ERROR id=%d message=missing_class", command_id);
    return;
  }

  if (confidence_value == NULL)
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(response, "ERROR id=%d message=missing_confidence", command_id);
    return;
  }

  if (!is_valid_class(class_value))
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(response, "ERROR id=%d message=invalid_class", command_id);
    return;
  }

  if (!parse_confidence(confidence_value, &confidence))
  {
    SorterState_Set(SORTER_STATE_ERROR);
    add_response_line(response, "ERROR id=%d message=invalid_confidence", command_id);
    return;
  }

  SorterState_Set(SORTER_STATE_COMMAND_RECEIVED);
  add_response_line(response, "ACK id=%d", command_id);

  SorterState_Set(SORTER_STATE_SORTING);
  response->accepted_sort = 1;

  SorterState_Set(SORTER_STATE_IDLE);
  add_response_line(response, "DONE id=%d", command_id);
}

static int is_valid_class(const char *class_name)
{
  return strcmp(class_name, "landfill") == 0 ||
         strcmp(class_name, "compost") == 0 ||
         strcmp(class_name, "recycling") == 0;
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
