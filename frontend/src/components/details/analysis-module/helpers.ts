export const prepareDatasetForMetrics = (metrics: any) => {
  return Object.entries(metrics).map(([service, values]: any) => ({
    service,
    micro_f1_score: values.micro_f1_score,
    micro_precision: values.micro_precision,
    micro_recall: values.micro_recall,
  }));
}

export const prepareDatasetForProbability = (probability: any) => {
  return Object.entries(probability).map(([service, values]: any) => ({
    service,
    faultyError: values.faultyError,
    faultyNoError: values.faultyNoError,
    goodError: values.goodError,
    goodNoError: values.goodNoError,
  }));
}