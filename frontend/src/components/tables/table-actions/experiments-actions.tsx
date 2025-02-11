'use client';
import Link from 'next/link';
import {
  Download,
  RefreshCcw,
  Copy,
  Eye,
  MoreHorizontal,
  Package,
} from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { useApi } from '@/hooks/use-api';
import { downloadFile } from '@/utils/download';

export const ExperimentsActions = ({
  experimentId,
  updateExperimentStatus,
}: {
  experimentId: string;
  updateExperimentStatus: (
    id: string,
    status: string,
    analysisStatus: string
  ) => void;
}) => {
  const { loading: loadingOnRefresh, fetchData: onRefreshStatus } = useApi({
    url: `/experiments/${experimentId}/status`,
    method: 'GET',
    manual: true,
  });

  const { loading: loadingDownloadZip, fetchData: onDownloadZip } = useApi({
    url: `/experiments/${experimentId}/data`,
    method: 'GET',
    manual: true,
  });

  const { loading: loadingDownloadFile, fetchData: onDownloadConfigFile } =
    useApi({
      url: `/experiments/${experimentId}/config`,
      method: 'GET',
      manual: true,
    });

  const handleRefreshStatus = async () => {
    const response: any = await onRefreshStatus();
    if (response) {
      updateExperimentStatus(
        experimentId,
        response.status,
        response.analysis_status
      );
    }
  };

  const handleDownload = async () => {
    const fileData = await onDownloadConfigFile();
    if (fileData) {
      const jsonBlob = new Blob([JSON.stringify(fileData, null, 2)], {
        type: 'application/json',
      });
      downloadFile(jsonBlob, `experiment-${experimentId}-config.json`);
    }
  };

  return (
    <div>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              disabled={loadingOnRefresh}
              variant='ghost'
              size='sm'
              onClick={handleRefreshStatus}
            >
              <RefreshCcw />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Refresh status</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              disabled={loadingDownloadZip}
              variant='ghost'
              size='sm'
              onClick={onDownloadZip}
            >
              <Package />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Download data as zip</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant='ghost' className='h-8 w-8 p-0'>
            <span className='sr-only'>Open menu</span>
            <MoreHorizontal className='h-4 w-4' />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align='end'>
          <DropdownMenuItem
            className='cursor-pointer'
            onClick={() => navigator.clipboard.writeText(experimentId)}
          >
            <Copy />
            Copy experiment ID
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem className='cursor-pointer'>
            <Eye />
            <Link href={`/experiments/${experimentId}`}>View details</Link>
          </DropdownMenuItem>

          <DropdownMenuItem className='cursor-pointer'>
            <Button disabled={loadingDownloadFile} onClick={handleDownload}>
              <Download />
              Download file
            </Button>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
};
