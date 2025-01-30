'use client';
import { useEffect, useState } from "react";
import { Cable, Save, Trash } from "lucide-react";
import { Button } from "../../../ui/button";
import CodeMirror from '@uiw/react-codemirror';
import { useApi } from "@/hooks/use-api";

interface EditableFileProps {
  file: File;
  parsedContent: object;
  onRemoveFile: () => void;
};

export const EditableFile: React.FC<EditableFileProps> = ({ file, parsedContent, onRemoveFile }) => {

  const [isFileCreated, setIsFileCreated] = useState(false);
  const [editableFile, setEditableFile] = useState(JSON.stringify(parsedContent, null, 2));
  const [experimentId, setExperimentId] = useState(null);

  const { data: responseAfterSave, error: errorOnCreate, loading: loadingOnCreate, fetchData: onCreateExperiment } = useApi({
    url: `/experiments`,
    method: "POST",
    body: {
      name: `${file.name}`,
      config: parsedContent
    }
  })

  const { data: responseOnStart, error: errorOnStart, loading: loadingOnStart, fetchData: onStartExperiment } = useApi({
    url: `/experiments/${experimentId}/runsync`,
    method: "POST",
    body: {
      runs: 1,
      output_format: "json"
    }
  })

  useEffect(() => {
    if (responseAfterSave) setExperimentId(responseAfterSave.id)
  }, [responseAfterSave])


  const handleFileCreate = () => {
    setIsFileCreated(true);
    onCreateExperiment();
  }

  const handleStartExperiment = () => {
    if (experimentId)
      onStartExperiment();
  }

  const onChange = (newFileValue: any) => {
    setEditableFile(newFileValue);
  };

  return (
    <div>
      <div className="text-sm text-gray-700 flex items-center justify-between">
        <span>Selected file: {file.name}</span>
        <Button variant="destructive" size="sm" onClick={() => onRemoveFile()}>
          <Trash />
        </Button>
      </div>

      <div className="mt-4">
        <h3 className="text-lg font-semibold mb-2">File Preview:</h3>
        <div className="max-h-[50vh] max-w-[850px] overflow-auto">
          <CodeMirror value={editableFile} theme="dark" editable onChange={onChange} />
        </div>
      </div>

      <div className="flex justify-end gap-2 my-4 w-full">
        <Button disabled={isFileCreated || loadingOnCreate} onClick={handleFileCreate} variant="outline">
          <Save />
          {isFileCreated ? 'File created!' : 'Create file'}
        </Button>

        <Button disabled={!isFileCreated || loadingOnStart} onClick={handleStartExperiment}>
          <Cable />
          Start Experiment
        </Button>
      </div>
    </div>
  );
};
