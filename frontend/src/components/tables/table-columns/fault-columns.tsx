import { ColumnDef } from '@tanstack/react-table';
import { Badge } from '@/components/ui/badge';
import { InfoIcon, TriangleAlert } from 'lucide-react';
import { formatDate } from '@/utils/date';

export const faultsColumns: ColumnDef<any>[] = [
  {
    accessorKey: 'start_time',
    header: 'Start Time',
    cell: ({ row }) => formatDate(row.original.start_time),
  },
  {
    accessorKey: 'end_time',
    header: 'End Time',
    cell: ({ row }) => formatDate(row.original.end_time),
  },
  { accessorKey: 'fault_name', header: 'Fault Name' },
  {
    accessorKey: 'detected',
    header: 'Detected?',
    cell: ({ row }) => (
      <Badge variant={row.original.detected ? 'default' : 'destructive'}>
        {row.original.detected ? 'Yes' : 'No'}
      </Badge>
    ),
  },
  {
    accessorKey: 'false_positives',
    header: 'False Positives #',
    cell: ({ row }) => {
      const hasFalsePositives = row.original.false_positives.length > 0;

      return (
        <div className='flex align-top gap-1 items-center justify-start'>
          {row.original.false_positives.length}
          {hasFalsePositives && <TriangleAlert size={16} color='red' />}
        </div>
      );
    },
  },
  {
    accessorKey: 'true_positives',
    header: 'True Positives #',
    cell: ({ row }) => {
      const hasTruePositives = row.original.true_positives.length > 0;
      return (
        <div className='flex align-top gap-1 items-center justify-start'>
          {row.original.true_positives.length}
          {hasTruePositives && <InfoIcon size={16} color='green' />}
        </div>
      );
    },
  },
  {
    accessorKey: 'detection_time',
    header: 'Detection Time',
    cell: ({ row }) => formatDate(row.original.detection_time),
  },
  {
    accessorKey: 'detection_latency',
    header: 'Detection Latency',
  },
];
