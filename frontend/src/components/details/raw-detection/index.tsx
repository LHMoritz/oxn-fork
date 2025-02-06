'use client';

import { useApi } from "@/hooks/use-api";
import { useEffect, useState } from "react";


export const RawDetection = ({ experimentId }: { experimentId: string }) => {

  const [rawDetectionData, setRawDetectionData] = useState([]);

  const { data } = useApi({
    url: `/experiments/${experimentId}/raw-detections`,
    method: "GET",
    showToast: false,
  });

  useEffect(() => {
    if (data) setRawDetectionData(data)
  }, [data])

  return (

    <div>
      <h4 className="text-lg font-semibold mb-4">Raw Detection Analysis</h4>
    </div>
  )
}