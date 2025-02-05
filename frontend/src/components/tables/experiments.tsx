'use client';
import { useEffect, useState } from "react";
import { experimentsColumns } from "./table-columns/experiments-columns";
import { useApi } from "@/hooks/use-api";
import { Button } from "../ui/button";
import { DynamicTable } from ".";

export const ExperimentsTable: React.FC<{}> = ({ }) => {

  const [experiments, setExperiments] = useState<any[]>([]);

  const { data, loading, error, fetchData } = useApi({ url: "/experiments" });

  useEffect(() => {
    if (data) setExperiments(data);
  }, [data]);

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

      {!loading && !error && <DynamicTable filterColumnKey="id" data={experiments} columns={experimentsColumns} />}
      {/* <DynamicTable filterColumnKey="id" data={experimentsMockData} columns={experimentsColumns} /> */}
    </div>
  )
}