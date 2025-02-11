'use client';
import { DynamicTable } from "@/components/tables"
import { analysisMetricsColumns, analysisProbabilityColumns } from "@/components/tables/table-columns/analysis-columns"
import { useApi } from "@/hooks/use-api"
import { useEffect, useState } from "react";
import { prepareDatasetForMetrics, prepareDatasetForProbability } from "./helpers";
import { MetricsChart } from "./metricsChart";
import { Button } from "@/components/ui/button";
import { ChartBar, Table } from "lucide-react";


export const AnalysisModule = ({ experimentId }: { experimentId: string }) => {

  const [viewMode, setViewMode] = useState<"table" | "chart">("table");
  const [metricsData, setMetricsData] = useState<any>([]);
  const [probabilityData, setProbabilityData] = useState<any>([]);

  const { data: analysisData, fetchData: onGetReport } = useApi({
    url: `analysis-data/${experimentId}`,
    method: "GET",
    manual: true,
  });

  useEffect(() => {
    if (analysisData && analysisData.metrics) {
      setMetricsData(prepareDatasetForMetrics(analysisData.metrics))
    }
    if (analysisData && analysisData.probability) {
      setProbabilityData(prepareDatasetForProbability(analysisData.probability))
    }
  }, [analysisData])


  return (
    <div>
      <div className="flex items-center align-middle justify-between mb-4 mt-4">
        <h3 className="text-lg font-semibold">Metrics Data</h3>
        <Button variant="secondary" size="default" onClick={() => setViewMode(viewMode === "table" ? "chart" : "table")}>
          {viewMode === "table" ? <span className="flex gap-2">
            <ChartBar />
            Display chart
          </span> : <span className="flex gap-2">
            <Table />
            Display table
          </span>}
        </Button>
      </div>
      {viewMode === "table" ? (
        <DynamicTable filterColumnKey={"service"} data={metricsData} columns={analysisMetricsColumns} />
      ) : (
        <MetricsChart data={metricsData} />
      )}

      <h3 className="text-lg font-semibold mb-2 mt-8">Probability Data</h3>
      <DynamicTable filterColumnKey={"service"} data={probabilityData} columns={analysisProbabilityColumns} />
    </div>
  )
}