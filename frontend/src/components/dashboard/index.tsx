import { Cog, MonitorCog, PackageCheck } from "lucide-react";
import { StartExperiment } from "./start-experiment";
import { UserManual } from "./user-manual";

export default function DashboardPage() {
  return (
    <div>
      <UserManual />
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
          experimentType="suite"
          icon={<MonitorCog />}
          description="lorem ipsum"
          title="Experiment Suite"
        />
      </div>
    </div>
  )
}