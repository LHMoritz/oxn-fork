import { ColumnDef } from "@tanstack/react-table"
import { formatDate } from "@/utils/date";
import { ExperimentsActions } from "../table-actions/experiments-actions";
import { Badge } from "@/components/ui/badge";

export const experimentsColumns = (updateExperimentStatus: (id: string, status: string, analysisStatus: string) => void): ColumnDef<any>[] => [
  {
    accessorKey: "id",
    header: "Experiment ID",
  },
  {
    accessorKey: "name",
    header: "Experiment name",
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
    header: "Experiment Status",
    cell: ({ row }) => <Badge className="mx-1">{row.original.status}</Badge>,
  },
  {
    accessorKey: "analysis_status",
    header: "Analysis Status",
    cell: ({ row }) => <Badge variant="outline" className="mx-1">{row.original.analysis_status}</Badge>,
  },
  {
    id: "actions",
    header: "Actions",
    cell: ({ row }) => <ExperimentsActions experimentId={row.original.id} updateExperimentStatus={updateExperimentStatus} />,
  },
];
