import { Cog, MonitorCog, PackageCheck } from "lucide-react";
import { StartExperiment } from "./start-experiment";
import { UserManual } from "./user-manual";

export default function DashboardPage() {
  return (
    <div>
      <UserManual />
      <div className="flex justify-evenly align-middle py-2">
        <StartExperiment
          experimentType="single"
          icon={<Cog />}
          description="Upload a single experiment file."
          title="Single Experiment" />
        <StartExperiment
          experimentType="batch"
          icon={<PackageCheck />}
          description="Upload a batch experiment file to generate multiple sub-experiments."
          title="Batch Experiments"
        />
        <StartExperiment
          experimentType="suite"
          icon={<MonitorCog />}
          description="Upload multiple single experiment files."
          title="Experiment Suite"
        />
      </div>
    </div>
  )
}