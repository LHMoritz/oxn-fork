'use client';
import { JSX, useEffect, useState } from "react";
import { ChartColumn, Sheet } from "lucide-react";
import { Button } from "../ui/button";
import { DynamicTable } from "../tables";
import { analysisColumns } from "../tables/table-columns/analysis-columns";
import { AnalysisChart } from "./chart";
import { useApi } from "@/hooks/use-api";

type ViewType = "chart" | "table";

export const AnalysisView = () => {

  const [selectedView, setSelectedView] = useState<ViewType>("chart");
  const [analysisData, setAnalysisData] = useState([]);

  const { data, loading, error, fetchData } = useApi({ url: "/analysis-data" });

  useEffect(() => {
    if (data) setAnalysisData(data);
  }, []);

  const views: { type: ViewType; label: string; icon: JSX.Element }[] = [
    { type: "chart", label: "Chart view", icon: <ChartColumn /> },
    { type: "table", label: "Table view", icon: <Sheet /> },
  ];


  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Experiment Analysis</h2>
      <div className="flex justify-between align-middle">
        <div>
          {views.map((view) => (
            <Button
              key={view.type}
              variant={selectedView === view.type ? "default" : "outline"}
              onClick={() => setSelectedView(view.type)}
            >
              {view.icon}
            </Button>
          ))}
        </div>
      </div>
      <div className="mt-4">
        {selectedView === "chart" && <AnalysisChart data={analysisData} />}
        {selectedView === "table" && <DynamicTable filterColumnKey={null} data={analysisData} columns={analysisColumns} />}
      </div>
    </div>
  )
}