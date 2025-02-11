'use client';
import { useEffect, useState } from 'react';
import { experimentsColumns } from './table-columns/experiments-columns';
import { useApi } from '@/hooks/use-api';
import { Button } from '../ui/button';
import { DynamicTable } from '.';

export const ExperimentsTable = () => {
  const [experiments, setExperiments] = useState<any[]>([]);

  const { data, loading, error, fetchData } = useApi({
    url: '/experiments',
    showToast: false,
  });

  useEffect(() => {
    if (data) setExperiments(data);
  }, [data]);

  const updateExperimentStatus = (
    experimentId: string,
    newStatus: string,
    newAnalysisStatus: string
  ) => {
    setExperiments((prevExperiments) =>
      prevExperiments.map((exp) =>
        exp.id === experimentId
          ? { ...exp, status: newStatus, analysis_status: newAnalysisStatus }
          : exp
      )
    );
  };

  return (
    <div>
      {error && (
        <div className='text-red-500 my-4'>
          <p>Error loading experiments: {error}</p>
          <Button onClick={fetchData} variant='outline'>
            Retry
          </Button>
        </div>
      )}

      {loading && <p>Loading experiments...</p>}

      {!loading && !error && (
        <DynamicTable
          filterColumnKey='id'
          data={experiments}
          columns={experimentsColumns(updateExperimentStatus)}
        />
      )}
    </div>
  );
};
