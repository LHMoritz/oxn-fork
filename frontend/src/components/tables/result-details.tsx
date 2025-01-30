'use client';
import { DynamicTable } from ".";
import { AnalysisView } from "../analysis";
import { resultDetailsColumns } from "./table-columns/result-details-columns";

export const ResultDetailsTable: React.FC<{}> = ({ }) => {

  return (
    <div>
      <DynamicTable filterColumnKey="runId" data={[]} columns={resultDetailsColumns} />
      <AnalysisView />
    </div>
  )
}