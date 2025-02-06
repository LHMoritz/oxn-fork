'use client';
import { DynamicTable } from "@/components/tables"
import { faultsColumns } from "./columns"
import { useApi } from "@/hooks/use-api";
import { useEffect, useState } from "react";
import { ExpandFaults } from "./expand-faults";

export const AnalyseFaultDetection = ({ experimentId }: { experimentId: string }) => {

  const [faultDetectionData, setFaultDetectionData] = useState<any>([]);

  const { data } = useApi({
    url: `/experiments/${experimentId}/analyse-fault-detection`,
    method: "GET",
    showToast: false,
  });

  useEffect(() => {
    if (data) setFaultDetectionData(data)
  }, [data])


  return (
    <div>
      <h4 className="text-lg font-semibold mb-4">Fault Detection Analysis</h4>
      <DynamicTable filterColumnKey="fault_name" data={faultDetectionData} columns={faultsColumns} />
    </div>
  )
}