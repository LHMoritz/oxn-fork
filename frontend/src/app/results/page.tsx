import { ReportsTable } from "@/components/tables/reports";

export default function ReportsPage() {
  return (
    <div>
      <div>
        <h1 className="text-xl font-bold">Reports</h1>
      </div>
      <div className="container mx-auto">
        <ReportsTable />
      </div>
    </div>
  )
};