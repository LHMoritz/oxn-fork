'use client';
import { useEffect, useState } from "react";
import { DynamicTable } from ".";
import { reportColumns } from "./table-columns/report-columns";
import { useApi } from "@/hooks/use-api";
import { Button } from "../ui/button";

export const ReportsTable: React.FC<{}> = ({ }) => {

  const [results, setResults] = useState<any[]>([]);

  const { data, loading, error, fetchData } = useApi({ url: "/results" });

  useEffect(() => {
    if (data) setResults(data);
  }, []);

  return (
    <div>
      {error && (
        <div className="text-red-500 my-4">
          <p>Error loading experiments: {error}</p>
          <Button onClick={fetchData} variant="outline">
            Retry
          </Button>
        </div>
      )}

      {loading && <p>Loading experiments...</p>}
      {!loading && !error && <DynamicTable data={results} columns={reportColumns} />}
    </div>
  )
}