import { ColumnDef } from "@tanstack/react-table"

export const analysisColumns: ColumnDef<any>[] = [
  {
    accessorKey: "variableName",
    header: "Service Name",
  },
  {
    accessorKey: "microprecision",
    header: "Micro Precision",
  },
  {
    accessorKey: "microrecall",
    header: "Micro Recall",
  },
  {
    accessorKey: "mircoF1Score",
    header: "Micro F1 Score",
  },
];
