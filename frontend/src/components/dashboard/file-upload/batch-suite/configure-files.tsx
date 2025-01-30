'use client';
import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Button } from "@/components/ui/button";
import { Cable, Save } from "lucide-react";
import { useApi } from "@/hooks/use-api";

interface ConfigureFilesProps {
  file: File;
  parsedContent: any;
  onRemoveFile: (index: number) => void;
}

export const ConfigureFiles: React.FC<ConfigureFilesProps> = ({
  file,
  parsedContent,
  onRemoveFile,
}) => {
  const [isFileCreated, setIsFileCreated] = useState(false);

  const [delayDuration, setDelayDuration] = useState<number>(0);
  const [instrumentationInterval, setInstrumentationInterval] = useState<number>(0);
  const [experimentId, setExperimentId] = useState(null);


  const { error: errorOnStart, loading: loadingOnStart, fetchData: onStartExperiment } = useApi({
    url: `/experiments`,
    method: "POST",
    body: {
      name: `${file.name}`,
      config: parsedContent
    }
  })

  const { error: errorOnCreate, loading: loadingOnCreate, fetchData: onCreateExperiment } = useApi({
    url: `/experiments/${experimentId}/batch`,
    method: "POST",
    body: {
      runs: 1,
      output_format: "json"
    }
  })


  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Delay Duration Input */}
        <div>
          <Label className="font-semibold" htmlFor="delayDuration">Delay Duration (ms)</Label>
          <Input
            id="delayDuration"
            type="number"
            value={delayDuration}
            onChange={(e) => setDelayDuration(Number(e.target.value))}
            placeholder="Enter delay duration in milliseconds"
          />
        </div>

        {/* Instrumentation Interval Input */}
        <div>
          <Label className="font-semibold" htmlFor="instrumentationInterval">Instrumentation Interval (ms)</Label>
          <Input
            id="instrumentationInterval"
            type="number"
            value={instrumentationInterval}
            onChange={(e) => setInstrumentationInterval(Number(e.target.value))}
            placeholder="Enter instrumentation interval in milliseconds"
          />
        </div>
      </div>

      <div className="w-[800px]">
        <SyntaxHighlighter language="yaml" style={oneDark} wrapLines>
          {JSON.stringify(parsedContent, null, 2)}
        </SyntaxHighlighter>
      </div>


      <div className="flex justify-end gap-2 my-4 w-full">
        <Button disabled={isFileCreated || loadingOnCreate} onClick={onCreateExperiment} variant="outline">
          <Save />
          {isFileCreated ? 'File created!' : 'Create file'}
        </Button>

        <Button disabled={!isFileCreated || loadingOnStart} onClick={onStartExperiment}>
          <Cable />
          Start Batch
        </Button>
      </div>
    </div>
  );
};
