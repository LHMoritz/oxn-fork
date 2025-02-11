import Chart from "react-apexcharts";

export const MetricsChart = ({ data }: { data: any }) => {

  const chartSeries = [
    {
      name: "Micro F1 Score",
      data: data.map((item: any) => item.micro_f1_score)
    },
    {
      name: "Micro Precision",
      data: data.map((item: any) => item.micro_precision)
    },
    {
      name: "Micro Recall",
      data: data.map((item: any) => item.micro_recall)
    }
  ];

  const chartOptions: any = {
    chart: {
      type: "bar"
    },
    xaxis: {
      categories: data.map((item: any) => item.service)
    },
    plotOptions: {
      bar: {
        horizontal: false
      }
    },
    dataLabels: {
      enabled: true
    }
  };

  return (
    <div>
      <Chart options={chartOptions} series={chartSeries} type="bar" height={350} />
    </div>
  )
}