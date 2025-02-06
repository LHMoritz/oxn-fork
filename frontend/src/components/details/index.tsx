'use client';

import { useApi } from "@/hooks/use-api";
import { Button } from "../ui/button";
import { AnalyseFaultDetection } from "./fault-detection";
import { RawDetection } from "./raw-detection";


export const ExperimentDetails = ({ experimentId }: { experimentId: string }) => {

  const { data: reportData, fetchData: onGetReport } = useApi({
    url: `/experiments/${experimentId}/report`,
    method: "GET",
    manual: true,
  });




  return (
    <div>
      <AnalyseFaultDetection experimentId={experimentId} />
      <RawDetection experimentId={experimentId} />
      <Button onClick={onGetReport}>Get Report</Button>
    </div>
  )
}