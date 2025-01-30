import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ResultDetailsTable } from "@/components/tables/result-details";


export default function ResultDetails(props: any) {

  const experimentId = props.params.experimentId;

  return (
    <div>
      <div className="flex justify-between">
        <h1 className="text-2xl font-bold">Details for #{experimentId}</h1>
        <div>
          <Button variant="ghost">
            <ChevronLeft />
            <Link href="/results">Go back</Link>
          </Button>
        </div>
      </div>
      <div className="container mx-auto">
        <ResultDetailsTable />
      </div>
    </div>
  )
}