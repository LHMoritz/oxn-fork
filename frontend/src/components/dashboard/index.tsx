import { Cog, MonitorCog, PackageCheck } from "lucide-react";
import { StartExperiment } from "./start-experiment";

export default function DashboardPage() {
  return (
    <div className="flex justify-evenly align-middle py-4">
      <StartExperiment
        experimentType="single"
        icon={<Cog />}
        description="lorem ipsum dolor sit amet"
        title="Single Experiment" />
      <StartExperiment
        experimentType="batch"
        icon={<PackageCheck />}
        description="lorem ipsum dolor sit amet"
        title="Batch Experiments"
      />
      <StartExperiment
        disabled
        experimentType="suite"
        icon={<MonitorCog />}
        description="Not available yet"
        title="Experiment Suite"
      />
    </div>
  )
}