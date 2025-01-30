'use client';
import { useState } from "react";
import { PreviewMultipleFiles } from "./preview-multiple-files";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ConfigureFilesProps {
  files: File[];
  parsedContents: any[];
  onRemoveFile: (index: number) => void;
  experimentType: string;
}

export const ConfigureFiles: React.FC<ConfigureFilesProps> = ({
  experimentType,
  files,
  parsedContents,
  onRemoveFile,
}) => {
  const [delayDuration, setDelayDuration] = useState<number>(0);
  const [instrumentationInterval, setInstrumentationInterval] = useState<number>(0);

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

      {/* Display Files */}
      <PreviewMultipleFiles
        experimentType={experimentType}
        files={files}
        parsedContents={parsedContents}
        onRemoveFile={onRemoveFile}
      />
    </div>
  );
};
