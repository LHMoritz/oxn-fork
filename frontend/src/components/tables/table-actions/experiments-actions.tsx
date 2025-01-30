"use client";
import { Download, RefreshCcw } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { useApi } from "@/hooks/use-api";

export const ExperimentsActions = ({ experimentId }: { experimentId: string }) => {

  const { loading: loadingOnRefresh, error: errorOnRefresh, fetchData: onRefreshStatus } = useApi({
    url: `/experiments/${experimentId}/status`,
    method: "GET",
    manual: true,
  });

  const { loading: loadingOnDownload, error: errorOnDownload, fetchData: onDownloadBenchmark } = useApi({
    url: `/experiments/${experimentId}/benchmark`,
    method: "GET",
    manual: true,
  });


  return (
    <div>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button disabled={loadingOnRefresh} variant="ghost" size="sm" onClick={onRefreshStatus}>
              <RefreshCcw />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Refresh experiment status</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>


      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button disabled={loadingOnDownload} variant="ghost" size="sm" onClick={onDownloadBenchmark}>
              <Download />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Download benchmark file</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  )
};

