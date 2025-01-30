import { ArrowUpDown } from "lucide-react";
import { ColumnDef } from "@tanstack/react-table"
import { Button } from "@/components/ui/button";
import { formatDate } from "@/utils/date";
import { ResultsActions } from "../table-actions/results-actions";
import { Badge } from "@/components/ui/badge";

export const reportColumns: ColumnDef<any>[] = [
  {
    accessorKey: "experimentDate",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }: any) => formatDate(row.original.experimentDate)
  },
  {
    accessorKey: "experimentId",
    header: "Experiment ID",
  },
  {
    accessorKey: "numberOfRuns",
    header: "# of Runs",
  },
  {
    accessorKey: "treatmentNames",
    header: "Treatment Names",
    cell: ({ row }: any) => {
      return (
        row.original.treatmentNames.map((name: string) => {
          return (
            <Badge variant="outline" className="mx-1">{name}</Badge>
          )
        })
      )
    }
  },
  {
    accessorKey: "treatmentTypes",
    header: "Treatment Types",
    cell: ({ row }: any) => {
      return (
        row.original.treatmentTypes.map((type: string) => {
          return (
            <Badge variant="secondary" className="mx-1">{type}</Badge>
          )
        })
      )
    }
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }: any) => {
      const experimentId = row.original.experimentId;
      return <ResultsActions experimentId={experimentId} />
    },
  },
];