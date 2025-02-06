import { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { InfoIcon } from "lucide-react";

export const faultsColumns: ColumnDef<any>[] = [
  { accessorKey: "fault_name", header: "Fault Name" },
  {
    accessorKey: "detected",
    header: "Detected?",
    cell: ({ row }) => (
      <Badge variant={row.original.detected ? "default" : "destructive"} >
        {row.original.detected ? "Yes" : "No"}
      </Badge>
    ),
  },
  {
    accessorKey: "false_positives",
    header: "False Positives #",
    cell: ({ row }) => {

      const hasFalsePositives = row.original.false_positives.length > 0

      return (
        <div className="flex align-top gap-1 items-center justify-start">
          {row.original.false_positives.length}
          {hasFalsePositives && <InfoIcon size={16} color="red" />}
        </div>
      )
    },
  },
  {
    accessorKey: "true_positives",
    header: "True Positives #",
    cell: ({ row }) => {

      const hasTruePositives = row.original.true_positives.length > 0
      return (
        <div>
          {row.original.true_positives.length}
          {hasTruePositives && <InfoIcon size={16} color="red" />}
        </div>
      )
    },
  },
  {
    accessorKey: "detection_time",
    header: "Detection Time",
  },
  {
    accessorKey: "detection_latency",
    header: "Detection Latency",
  },
];