import { ArrowUpDown, Badge } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table"
import { Button } from "@/components/ui/button";
import { formatDate } from "@/utils/date";

export const reportDetailsColumns: ColumnDef<any>[] = [
  {
    accessorKey: 'runDate',
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}>
          Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => formatDate(row.original.runDate),
  },
  {
    accessorKey: 'runId',
    header: 'Run ID',
  },
  {
    accessorKey: 'interactionId',
    header: 'Interaction ID',
  },
  {
    accessorKey: "treatmentName",
    header: "Treatment Name",
    cell: ({ row }: any) => {
      return <Badge className="mx-1">{row.original.treatmentName}</Badge>
    }
  },
  {
    accessorKey: "treatmentType",
    header: "Treatment Type",
    cell: ({ row }: any) => {
      return <Badge className="mx-1">{row.original.treatmentType}</Badge>
    }
  },
  {
    accessorKey: 'treatmentStart',
    header: 'Treatment Start',
    cell: ({ row }) => formatDate(row.original.treatmentStart),
  },
  {
    accessorKey: 'treatmentEnd',
    header: 'Treatment End',
    cell: ({ row }) => formatDate(row.original.treatmentEnd),
  },
  {
    accessorKey: 'responseName',
    header: 'Response Name',
  },
  {
    accessorKey: 'responseType',
    header: 'Response Type',
  },
  // {
  //   accessorKey: 'loadgenStartTime',
  //   header: 'Loadgen Start Time',
  //   cell: ({ row }) => formatDate(row.original.loadgenStartTime),
  // },
  // {
  //   accessorKey: 'loadgenEndTime',
  //   header: 'Loadgen End Time',
  //   cell: ({ row }) => formatDate(row.original.loadgenEndTime),
  // },
  {
    accessorKey: 'loadgenTotalRequests',
    header: 'Total Requests',
  },
  {
    accessorKey: 'loadgenTotalFailures',
    header: 'Total Failures',
  },
];