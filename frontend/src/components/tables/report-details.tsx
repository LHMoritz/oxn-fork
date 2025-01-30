'use client';
import { DynamicTable } from ".";
import { AnalysisView } from "../analysis";
import { reportDetailsColumns } from "./table-columns/report-details-columns";

export const ReportDetailsTable: React.FC<{}> = ({ }) => {

  return (
    <div>
      <DynamicTable filterColumnKey="runId" data={[]} columns={reportDetailsColumns} />
      <AnalysisView />
    </div>
  )
}