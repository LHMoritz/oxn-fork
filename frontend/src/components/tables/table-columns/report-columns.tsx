import { formatDate } from '@/utils/date';
import { ColumnDef } from '@tanstack/react-table';

export const reportColumns: ColumnDef<any>[] = [
  {
    accessorKey: 'runId',
    header: 'Run ID',
  },
  {
    accessorKey: 'interactionId',
    header: 'Interaction ID',
  },
  // {
  //   accessorKey: "response_start",
  //   header: "Response Start",
  //   cell: ({ row }) => formatDate(row.original.response_start),
  // },
  // {
  //   accessorKey: "response_end",
  //   header: "Response End",
  //   cell: ({ row }) => formatDate(row.original.response_end),
  // },
  {
    accessorKey: 'response_name',
    header: 'Response Name',
  },
  {
    accessorKey: 'response_type',
    header: 'Response Type',
  },
  // {
  //   accessorKey: "store_key",
  //   header: "Store Key",
  // },
  {
    accessorKey: 'treatment_start',
    header: 'Treatment Start',
    cell: ({ row }) => formatDate(row.original.treatment_start),
  },
  {
    accessorKey: 'treatment_end',
    header: 'Treatment End',
    cell: ({ row }) => formatDate(row.original.treatment_end),
  },
  {
    accessorKey: 'treatment_name',
    header: 'Treatment Name',
  },
  {
    accessorKey: 'treatment_type',
    header: 'Treatment Type',
  },
];
