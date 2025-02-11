/* eslint-disable  @typescript-eslint/no-explicit-any */
'use client';
import { DynamicTable } from '@/components/tables';
import { useApi } from '@/hooks/use-api';
import { useEffect, useState } from 'react';
import { transformReportData } from './helpers';
import { reportColumns } from '@/components/tables/table-columns/report-columns';
import { formatDate } from '@/utils/date';

export const Report = ({ experimentId }: { experimentId: string }) => {
  const [reportData, setReportData] = useState<any>([]);

  const { data } = useApi({
    url: `/experiments/${experimentId}/report`,
    method: 'GET',
  });

  useEffect(() => {
    if (data && data.report) setReportData(transformReportData(data.report));
  }, [data]);

  return (
    <div>
      <h2 className='text-lg font-semibold mb-4'>
        Report for Experiment #{experimentId}
      </h2>
      <div className='text-sm font-bold border p-2'>
        <p>Experiment start time: {formatDate(reportData?.experiment_start)}</p>
        <p>Experiment end time: {formatDate(reportData?.experiment_end)}</p>
      </div>
      <DynamicTable
        filterColumnKey='runId'
        data={reportData}
        columns={reportColumns}
      />
    </div>
  );
};
