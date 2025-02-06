"use client";
import { useState } from "react";
import { FileText, ChevronDown, ChevronUp, Trash, Cable } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useApi } from "@/hooks/use-api";
import CodeMirror from "@uiw/react-codemirror";
import { yaml } from "@codemirror/lang-yaml";
import { json } from "@codemirror/lang-json";
import { useTheme } from "next-themes";

interface SuiteFilesProps {
  files: File[];
}

export const SuiteFiles: React.FC<SuiteFilesProps> = ({ files }) => {
  const [expandedFileIndex, setExpandedFileIndex] = useState<number | null>(null);
  const [fileContents, setFileContents] = useState<{ [key: number]: string }>({});
  const [fileTypes, setFileTypes] = useState<{ [key: number]: "yaml" | "json" | null }>({});
  const { theme } = useTheme();

  const { fetchData: onStartSuite } = useApi({
    // TODO: Replace with suite API
    url: "/experiments/suite",
    method: "POST",
    body: [],
  });

  const toggleFileExpansion = (index: number, file: File) => {
    if (expandedFileIndex === index) {
      setExpandedFileIndex(null);
      return;
    }

    if (!fileContents[index]) {
      const reader = new FileReader();
      reader.onload = (event) => {
        const content = event.target?.result as string;
        setFileContents((prev) => ({ ...prev, [index]: content }));

        if (file.name.endsWith(".yaml") || file.name.endsWith(".yml")) {
          setFileTypes((prev) => ({ ...prev, [index]: "yaml" }));
        } else if (file.name.endsWith(".json")) {
          setFileTypes((prev) => ({ ...prev, [index]: "json" }));
        }
      };
      reader.readAsText(file);
    }

    setExpandedFileIndex(index);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">Files Preview</h2>
      <ScrollArea className="h-full w-full border rounded-md p-2">
        {files.map((file, index) => (
          <div key={index} className="mb-2">
            <div className="flex justify-between">
              <div className="flex items-center gap-2">
                <FileText size={18} />
                {file.name}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => toggleFileExpansion(index, file)}>
                  {expandedFileIndex === index ? (
                    <div className="flex items-center gap-1">
                      <span>Collapse</span>
                      <ChevronUp size={20} />
                    </div>
                  ) : (
                    <div className="flex items-center gap-1">
                      <span>Expand</span>
                      <ChevronDown size={20} />
                    </div>
                  )}
                </Button>
              </div>
            </div>

            {expandedFileIndex === index && (
              <div className="p-3 w-[800px]">
                {fileContents[index] && fileTypes[index] && (
                  <CodeMirror
                    value={fileContents[index]}
                    editable={false}
                    extensions={[fileTypes[index] === "yaml" ? yaml() : json()]}
                    theme={theme === "light" ? "light" : "dark"}
                  />
                )}
              </div>
            )}
          </div>
        ))}
      </ScrollArea>

      <div className="flex justify-end gap-2 my-4 w-full">
        <Button disabled={true} onClick={onStartSuite}>
          <Cable />
          Start Suite
        </Button>
      </div>
    </div>
  );
};
