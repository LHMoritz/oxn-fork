import { ColumnDef } from "@tanstack/react-table"

export const analysisMetricsColumns: ColumnDef<any>[] = [
  {
    accessorKey: 'service',
    header: 'Service',
  },
  {
    accessorKey: 'micro_f1_score',
    header: 'Micro F1 Score',
  },
  {
    accessorKey: 'micro_precision',
    header: 'Micro Precision',
  },
  {
    accessorKey: 'micro_recall',
    header: 'Micro Recall',
  },
];

export const analysisProbabilityColumns: ColumnDef<any>[] = [
  {
    accessorKey: 'service',
    header: 'Service',
  },
  {
    accessorKey: 'faultyError',
    header: 'Faulty Error',
  },
  {
    accessorKey: 'faultyNoError',
    header: 'Faulty No Error',
  },
  {
    accessorKey: 'goodError',
    header: 'Good Error',
  },
  {
    accessorKey: 'goodNoError',
    header: 'Good No Error',
  },
];

