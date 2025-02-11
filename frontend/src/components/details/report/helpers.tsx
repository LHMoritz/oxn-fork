interface RunData {
  interactions: Record<string, any>;
}

export function transformReportData(report: any): any[] {
  const rows: any[] = [];
  if (report && report.runs) {
    const runs = report.runs as Record<string, RunData>;
    for (const [runId, runData] of Object.entries(runs)) {
      if (runData && runData.interactions) {
        for (const [interactionId, interaction] of Object.entries(runData.interactions)) {
          rows.push({
            runId,
            interactionId,
            response_end: (interaction as any).response_end,
            response_name: (interaction as any).response_name,
            response_start: (interaction as any).response_start,
            response_type: (interaction as any).response_type,
            store_key: (interaction as any).store_key,
            treatment_end: (interaction as any).treatment_end,
            treatment_name: (interaction as any).treatment_name,
            treatment_start: (interaction as any).treatment_start,
            treatment_type: (interaction as any).treatment_type,
          });
        }
      }
    }
  }
  return rows;
}
