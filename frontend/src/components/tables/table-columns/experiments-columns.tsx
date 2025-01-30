import { ColumnDef } from "@tanstack/react-table"
import { formatDate } from "@/utils/date";
import { ExperimentsActions } from "../table-actions/experiments-actions";
import { Badge } from "@/components/ui/badge";

export const experimentsColumns: ColumnDef<any>[] = [
  {
    accessorKey: "id",
    header: "Experiment ID",
  },
  {
    accessorKey: "name",
    header: "Experiment name",
  },
  {
    accessorKey: "created_at",
    header: "Created at",
    cell: ({ row }) => formatDate(row.original.created_at),
  },
  {
    accessorKey: "started_at",
    header: "Started at",
    cell: ({ row }) => formatDate(row.original.started_at),
  },
  {
    accessorKey: "completed_at",
    header: "Completed at",
    cell: ({ row }) => formatDate(row.original.completed_at),
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }: any) => {
      return <Badge className="mx-1">{row.original.status}</Badge>
    }
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }: any) => {
      return <ExperimentsActions experimentId={row.original.id} />
    }
  }
];