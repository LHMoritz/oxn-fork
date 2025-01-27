"use client";
import { ExperimentType } from "@/types";
import { ExperimentsTable } from "@/components/dynamic-table/table"
import { allResultsConfig } from "@/components/dynamic-table/table-columns"
import { useState, useEffect } from "react";
import { useApi } from "@/hooks/use-api";
import { prepareResultsTableData } from "@/utils/results";

export default function ResultsPage() {
  const [tableData, setTableData] = useState<ExperimentType[]>([]);
  const { get, loading } = useApi();

  const fetchResults = async () => {
    try {
      const response = await get("/results");
      const preparedData = prepareResultsTableData(response);
      setTableData(preparedData);
    } catch (error) {
      console.error("Error fetching results:", error);
    }
  };

  useEffect(() => {
    fetchResults();
  }, []);

  return (
    <div>
      <div>
        <h1 className="text-xl font-bold">All Experiment Results</h1>
      </div>
      <div className="container mx-auto">
        <ExperimentsTable columns={allResultsConfig} data={tableData} />
      </div>
    </div>
  )
}