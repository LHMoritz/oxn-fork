import Link from "next/link";

import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Copy, Download, Eye, MoreHorizontal } from "lucide-react";
import { useApi } from "@/hooks/use-api";

export const ResultsActions = ({ experimentId }: { experimentId: string }) => {

  const { loading: loadingOnDownload, error: errorOnDownload, fetchData: onDownloadReport } = useApi({
    url: `/experiments/${experimentId}/report`,
    method: "GET",
    manual: true,
  });

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="h-8 w-8 p-0">
          <span className="sr-only">Open menu</span>
          <MoreHorizontal className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">

        <DropdownMenuItem
          className="cursor-pointer"
          onClick={() => navigator.clipboard.writeText(experimentId)}
        >
          <Copy />
          Copy experiment ID
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="cursor-pointer">
          <Eye />
          <Link href={`/results/${experimentId}`}>View details</Link>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <Button disabled={loadingOnDownload} onClick={onDownloadReport}>
            <Download />
            Download file
          </Button>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}