import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel"
import { BookOpenText } from "lucide-react"

export const UserManual = () => {
  return (
    <div className="flex items-center justify-center p-8">
      <Card className="w-full">
        <CardHeader className="px-6">
          <CardTitle className="flex align-top items-center text-2xl font-bold gap-2">
            <BookOpenText />
            Step-by-step Guide to Experiment Configuration
          </CardTitle>
          <CardDescription className="mt-2 text-gray-600">
            Follow these detailed instructions to set up your experiments with ease.
          </CardDescription>
        </CardHeader>
        <CardContent className="px-6">
          <Carousel>
            <CarouselContent>
              <CarouselItem>
                <h3 className="text-lg font-semibold text-indigo-600">Step 1: Select the Experiment Type</h3>
                <div className="py-2">
                  <p className="py-2">
                    <span className="font-bold">Single: </span>
                    Upload a single experiment file. You can review and edit its parameters if needed before running.
                  </p>
                  <p className="py-2">
                    <span className="font-bold">Batch: </span>
                    Upload a batch experiment file to generate multiple sub-experiments. Use dot syntax to define parameter variations (e.g., <code className="bg-gray-100 px-1 rounded">experiment.treatments.1.delay_treatment.params.duration: ["1m", "2m"]</code>). The system creates a cross-product of these variations, producing different parameter combinations.
                  </p>
                  <p className="py-2">
                    <span className="font-bold">Suite: </span>
                    Upload multiple single experiment files. You can view them after uploading, but editing is not possible. Experiments run sequentially.
                  </p>
                </div>
              </CarouselItem>
              <CarouselItem className="px-4">
                <h3 className="text-xl font-semibold text-indigo-600">Step 2: Upload the Experiment Configuration File (YAML or JSON)</h3>
                <p>
                  Refer to our documentation for guidance on how to structure your YAML or JSON file for a robust observability experiment.
                </p>
              </CarouselItem>
              <CarouselItem className="px-4">
                <h3 className="text-xl font-semibold text-indigo-600">Step 3: Create Experiment</h3>
                <p>
                  Once your file is uploaded and edited (in case of <i>Single</i> or <i>Batch</i> experiments), click the "Create file" button to create the experiment configuration before starting the experiment.
                </p>
              </CarouselItem>
              <CarouselItem className="px-4">
                <h3 className="text-xl font-semibold text-indigo-600">Step 4: Start the Experiment</h3>
                <p>
                  Once your configuration is set, click the "Start Experiment" button to begin the process.
                </p>
              </CarouselItem>
              <CarouselItem className="px-4">
                <h3 className="text-xl font-semibold text-indigo-600">Step 5: Review the Results</h3>
                <p>
                  After completion, navigate to the Experiments tab to review the detailed results, metrics, and logs.
                </p>
              </CarouselItem>
            </CarouselContent>
            <CarouselPrevious />
            <CarouselNext />
          </Carousel>
        </CardContent>
        <CardFooter className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 text-right">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Need more help? Checkout our full report.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};
