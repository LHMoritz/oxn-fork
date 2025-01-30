export function getChartOptions(data: any) {

  return {
    chart: {
      type: "bar",
      toolbar: {
        show: true,
      },
    },
    dataLabels: {
      enabled: false,
    },
    colors: ["#e21d48", "#2563ea", "#16a449"],
    xaxis: {
      labels: {
        formatter: (value: string) => (value.length > 10 ? value.substring(0, 10) + "..." : value),
      },
      categories: data.map((el: any) => el.variableName),
      title: {
        text: "Services",
      },
    },
    yaxis: {
      title: { text: "Score" },
      min: 0,
      max: 1,
    },
    plotOptions: {
      bar: { horizontal: false, columnWidth: "50%" },
    },
    tooltip: {
      x: {
        formatter: (value: string) => value,
      },
      y: {}
    },
    legend: { position: "top" },
  };
}

export function getChartSeries(data: any) {
  return [
    {
      name: "Micro Precision",
      data: data.map((el: any) => el.microprecision),
    },
    {
      name: "Micro Recall",
      data: data.map((el: any) => el.microrecall),
    },
    {
      name: "Micro F1 Score",
      data: data.map((el: any) => el.mircoF1Score),
    },
  ];
}

