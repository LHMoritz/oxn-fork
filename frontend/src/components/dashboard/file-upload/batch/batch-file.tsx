'use client';
import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import CodeMirror from '@uiw/react-codemirror';
import { yaml as yamlFormat } from "@codemirror/lang-yaml";
import { json as jsonFormat } from "@codemirror/lang-json";
import { Button } from "@/components/ui/button";
import { Cable, Save } from "lucide-react";
import { useApi } from "@/hooks/use-api";
import { useTheme } from "next-themes";
import yaml from "js-yaml";

interface BatchFileProps {
  file: File;
}

export const BatchFile: React.FC<BatchFileProps> = ({ file }) => {

  const [previewFile, setPreviewFile] = useState<string | null>(null);
  const [fileType, setFileType] = useState<"yaml" | "json" | null>(null);
  const [isFileCreated, setIsFileCreated] = useState(false);
  const [batchId, setBatchId] = useState(null);
  const { theme } = useTheme();

  const parsedConfig = fileType === "yaml" ? yaml.load(previewFile || "") : JSON.parse(previewFile || "{}");

  const { data: responseAfterCreate, loading: loadingOnCreate, fetchData: onCreateBatchExperiments } = useApi({
    url: `/experiments/batch`,
    method: "POST",
    body: parsedConfig,
  })

  const { loading: loadingOnStartBatch, fetchData: onStartBatchExperiments } = useApi({
    url: `/experiments/batch/${batchId}/run`,
    method: "POST",
    body: {
      runs: 1,
      output_formats: [
        "json"
      ]
    }
  })


  useEffect(() => {
    if (responseAfterCreate) setBatchId(responseAfterCreate.id)
  }, [responseAfterCreate])

  useEffect(() => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setPreviewFile(content);

      if (file.name.endsWith(".yaml") || file.name.endsWith(".yml")) {
        setFileType("yaml");
      } else if (file.name.endsWith(".json")) {
        setFileType("json");
      }
    };
    reader.readAsText(file);
  }, [file]);


  const handleFileCreate = () => {
    setIsFileCreated(true);
    onCreateBatchExperiments();
  }

  const handleStartExperiment = () => {
    if (batchId)
      onStartBatchExperiments();
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        BATCH COMPONENT
      </div>

      <div className="w-[800px]">
        {previewFile && <CodeMirror
          value={previewFile}
          editable={false}
          extensions={[fileType === "yaml" ? yamlFormat() : jsonFormat()]}
          theme={theme === "light" ? "light" : "dark"}
        />}
      </div>


      <div className="flex justify-end gap-2 my-4 w-full">
        <Button disabled={isFileCreated || loadingOnCreate} onClick={handleFileCreate} variant="outline">
          <Save />
          {isFileCreated ? 'File created!' : 'Create file'}
        </Button>

        <Button disabled={!isFileCreated || loadingOnStartBatch} onClick={handleStartExperiment}>
          <Cable />
          Start Batch
        </Button>
      </div>
    </div>
  );
};
