#ifndef SORTER_TYPES_H
#define SORTER_TYPES_H

typedef enum
{
  SORTER_CLASS_UNKNOWN = 0,
  SORTER_CLASS_LANDFILL,
  SORTER_CLASS_COMPOST,
  SORTER_CLASS_RECYCLING
} SorterClass;

SorterClass SorterClass_FromString(const char *class_name);
const char *SorterClass_ToString(SorterClass class_name);

#endif /* SORTER_TYPES_H */
