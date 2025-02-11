'use client';

import { useApi } from "@/hooks/use-api";
import { AnalyseFaultDetection } from "./fault-detection";
import { Report } from "./report";
import { useEffect, useState } from "react";
import { STATUS } from "@/types";
import { AnalysisModule } from "./analysis-module";
import { Button } from "../ui/button";
import { RefreshCcw } from "lucide-react";


export const ExperimentDetails = ({ experimentId }: { experimentId: string }) => {
  const { data: statusData, fetchData: onGetStatus } = useApi({
    url: `/experiments/${experimentId}/status`,
    method: "GET",
    showToast: false,
  });

  const [hasAdditionalReports, setHasAdditionalReports] = useState(false);

  useEffect(() => {
    if (statusData && statusData.analysis_status !== STATUS.NOT_ENABLED) {
      setHasAdditionalReports(true)
    }
  }, [statusData]);


  return (
    <div>
      <div className="flex justify-end">
        <Button variant="outline" onClick={onGetStatus}>
          <RefreshCcw />
          Refresh Status
        </Button>
      </div>
      {hasAdditionalReports && <AnalyseFaultDetection experimentId={experimentId} />}
      {hasAdditionalReports && <AnalysisModule experimentId={experimentId} />}
      <Report experimentId={experimentId} />
    </div>
  )
}