"use client";

import dynamic from "next/dynamic";
import { getChartOptions, getChartSeries } from "./chart-config";
const Chart = dynamic(() => import("react-apexcharts"), { ssr: false });

export const AnalysisChart = ({ data }: { data: any[] }) => {

  const options: any = getChartOptions(data);
  const series: any = getChartSeries(data);

  return (
    <div className="w-full">
      <Chart options={options} series={series} type="bar" height={400} />
    </div>
  );
}
