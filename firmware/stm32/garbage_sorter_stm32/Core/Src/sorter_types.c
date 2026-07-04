#include "sorter_types.h"

#include <string.h>

SorterClass SorterClass_FromString(const char *class_name)
{
  if (class_name == NULL)
  {
    return SORTER_CLASS_UNKNOWN;
  }

  if (strcmp(class_name, "landfill") == 0)
  {
    return SORTER_CLASS_LANDFILL;
  }

  if (strcmp(class_name, "compost") == 0)
  {
    return SORTER_CLASS_COMPOST;
  }

  if (strcmp(class_name, "recycling") == 0)
  {
    return SORTER_CLASS_RECYCLING;
  }

  return SORTER_CLASS_UNKNOWN;
}

const char *SorterClass_ToString(SorterClass class_name)
{
  switch (class_name)
  {
    case SORTER_CLASS_LANDFILL:
      return "landfill";
    case SORTER_CLASS_COMPOST:
      return "compost";
    case SORTER_CLASS_RECYCLING:
      return "recycling";
    case SORTER_CLASS_UNKNOWN:
    default:
      return "unknown";
  }
}
