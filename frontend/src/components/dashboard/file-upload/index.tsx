"use client";
import React, { useState } from "react";
import yaml from "js-yaml";
import Dropzone from "./dropzone";
import { EditableFile } from "./single/editable-file";
import { PreviewMultipleFiles } from "./batch-suite/preview-multiple-files";
import { Button } from "@/components/ui/button";
import { Trash, Upload } from "lucide-react";
import { ConfigureFiles } from "./batch-suite/configure-files";

interface FileUploaderProps {
  experimentType: string;
  filesAccepted?: string[];
  allowMultiple?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  filesAccepted = [".yaml"],
  experimentType,
  allowMultiple = false,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [parsedContents, setParsedContents] = useState<object[]>([]);

  const noFilesUploaded = selectedFiles.length === 0;
  const filesUploaded = selectedFiles.length > 0;
  const noFilesParsed = parsedContents.length === 0;
  const filesParsed = parsedContents.length > 0;

  const handleFileSelect = (files: File[] | File) => {
    const filesArray = Array.isArray(files) ? files : [files];
    setSelectedFiles(filesArray);
    setParsedContents([]); // Reset parsed contents when selecting new files
  };

  const handleUpload = () => {
    if (selectedFiles.length > 0) {
      const newParsedContents: object[] = [];
      selectedFiles.forEach((file) => {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const yamlContent = event.target?.result as string;
            const parsedData: any = yaml.load(yamlContent);
            newParsedContents.push(parsedData);
            if (newParsedContents.length === selectedFiles.length) {
              setParsedContents(newParsedContents);
            }
          } catch (error) {
            console.error("Error parsing YAML file:", error);
          }
        };
        reader.readAsText(file);
      });
    }
  };

  const handleRemoveFile = (fileIndex: number) => {
    // Remove the file at the given index
    const updatedFiles = selectedFiles.filter((_, index) => index !== fileIndex);
    setSelectedFiles(updatedFiles);

    // Also remove the corresponding parsed content if it exists
    if (parsedContents.length > 0) {
      const updatedParsedContents = parsedContents.filter((_, index) => index !== fileIndex);
      setParsedContents(updatedParsedContents);
    }
  };

  return (
    <div>
      {noFilesUploaded && (
        <Dropzone
          onFileSelect={handleFileSelect}
          filesAccepted={filesAccepted}
          allowMultiple={allowMultiple}
        />
      )}

      {/* Show Upload Button when a file is uploaded but not yet parsed */}
      {filesUploaded && noFilesParsed && (
        <div>
          {selectedFiles.map((file, index) => {
            return (
              <div
                className="text-sm text-gray-700 flex items-center justify-between py-2"
                key={index}
              >
                <span>Selected file: {file.name}</span>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => handleRemoveFile(index)}
                >
                  <Trash />
                </Button>
              </div>
            );
          })}
          <div className="flex justify-center mt-4">
            <Button size="lg" onClick={handleUpload}>
              <Upload />
              Upload
            </Button>
          </div>
        </div>
      )}

      {experimentType === "single" && filesUploaded && filesParsed && (
        <EditableFile file={selectedFiles[0]} parsedContent={parsedContents[0]} onRemoveFile={() => handleRemoveFile(0)} />
      )}
      {experimentType === "batch" && filesUploaded && filesParsed && (
        <ConfigureFiles experimentType={experimentType} files={selectedFiles} parsedContents={parsedContents} onRemoveFile={handleRemoveFile} />
      )}
      {experimentType === "suite" && filesUploaded && filesParsed && (
        <PreviewMultipleFiles experimentType={experimentType} onRemoveFile={handleRemoveFile} files={selectedFiles} parsedContents={parsedContents} />
      )}
    </div>
  );
};
