import { ResultsTable } from "@/components/tables/results";

export default function ResultsPage() {
  return (
    <div>
      <div>
        <h1 className="text-xl font-bold">Results</h1>
      </div>
      <div className="container mx-auto">
        <ResultsTable />
      </div>
    </div>
  )
};