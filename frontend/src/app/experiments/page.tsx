import { ExperimentsTable } from "@/components/tables/experiments";

export default function ExperimentsPage() {
  return (
    <div>
      <div>
        <h1 className="text-xl font-bold">Experiment Configurations</h1>
      </div>
      <div className="container mx-auto">
        <ExperimentsTable />
      </div>
    </div>
  )
};