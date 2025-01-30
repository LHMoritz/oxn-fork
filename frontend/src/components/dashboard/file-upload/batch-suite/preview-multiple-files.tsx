"use client";

import { useState } from "react";
import { FileText, ChevronDown, ChevronUp, Trash, Save, Cable } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark, oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useTheme } from "next-themes";

interface PreviewMultipleFilesProps {
  files: File[];
  parsedContents: any[];
  onRemoveFile: (index: number) => void;
  experimentType: string;
}

export const PreviewMultipleFiles: React.FC<PreviewMultipleFilesProps> = ({ experimentType, files, parsedContents, onRemoveFile }) => {
  const { theme } = useTheme();
  const [expandedFileIndex, setExpandedFileIndex] = useState<number | null>(null);
  const [isSavedFile, setIsSavedFile] = useState(false);

  const onCreateExperiment = async () => {
    alert('Creating experiment...');
  };

  const onStartExperiment = async () => {
    alert('Starting experiment...');
  }

  const handleFileSave = () => {
    setIsSavedFile(true);
    onCreateExperiment();
  }

  const handleStartExperiment = () => {
    onStartExperiment();
  }

  const toggleFileExpansion = (index: number) => {
    setExpandedFileIndex(expandedFileIndex === index ? null : index);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Files Preview</h2>
      <ScrollArea className="h-full w-full border rounded-md p-2">
        {files.map((file, index) => (
          <div key={index} className='mb-2'>
            <div className='flex justify-between'>
              <div className="flex items-center gap-2">
                <FileText size={18} />
                {file.name}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => toggleFileExpansion(index)}>
                  {expandedFileIndex === index ? <div className="flex items-center gap-1">
                    <span>Collapse</span>
                    <ChevronUp size={20} />
                  </div> :
                    <div className="flex items-center gap-1">
                      <span>Expand</span>
                      <ChevronDown size={20} />
                    </div>}
                </Button>

                <Button size="sm" variant="destructive" onClick={() => onRemoveFile(index)}>
                  <Trash />
                </Button>
              </div>
            </div>
            {expandedFileIndex === index && (
              <div className="p-3 w-[800px]">
                <SyntaxHighlighter language="yaml" style={theme === "dark" ? oneDark : oneLight} wrapLines>
                  {JSON.stringify(parsedContents[index], null, 2)}
                </SyntaxHighlighter>
              </div>
            )}
          </div>
        ))}
      </ScrollArea>

      <div className="flex justify-end gap-2 my-4 w-full">
        <Button disabled={isSavedFile} onClick={handleFileSave} variant="outline">
          <Save />
          {isSavedFile ? 'File saved!' : 'Save file'}
        </Button>

        <Button disabled={!isSavedFile} onClick={handleStartExperiment}>
          <Cable />
          Start Experiment
        </Button>
      </div>
    </div>
  );
};
