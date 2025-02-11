'use client';
import React, { useState } from 'react';
import Dropzone from './dropzone';
import { SingleFile } from './single/single-file';
import { BatchFile } from './batch/batch-file';
import { SuiteFiles } from './suite/suite-files';
import { Button } from '@/components/ui/button';
import { Trash } from 'lucide-react';

interface FileUploaderProps {
  experimentType: string;
  filesAccepted?: string[];
  allowMultiple?: boolean;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  filesAccepted = ['.yaml', '.json'],
  experimentType,
  allowMultiple = false,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);

  const noFilesUploaded = selectedFiles.length === 0;
  const filesUploaded = selectedFiles.length > 0;

  const handleFileSelect = (files: File[] | File) => {
    setSelectedFiles((prevFiles) => {
      const filesArray = Array.isArray(files) ? files : [files];
      return allowMultiple ? [...prevFiles, ...filesArray] : filesArray;
    });
  };

  const handleRemoveFile = (fileIndex: number) => {
    const updatedFiles = selectedFiles.filter(
      (_, index) => index !== fileIndex
    );
    setSelectedFiles(updatedFiles);
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

      {filesUploaded && (
        <div>
          {selectedFiles.map((file, index) => {
            return (
              <div
                className='text-sm text-gray-700 flex items-center justify-between py-2'
                key={index}
              >
                <span>Selected file: {file.name}</span>
                <Button
                  variant='destructive'
                  size='sm'
                  onClick={() => handleRemoveFile(index)}
                >
                  <Trash />
                </Button>
              </div>
            );
          })}
        </div>
      )}

      {experimentType === 'single' && filesUploaded && (
        <SingleFile file={selectedFiles[0]} />
      )}
      {experimentType === 'batch' && filesUploaded && (
        <BatchFile file={selectedFiles[0]} />
      )}
      {experimentType === 'suite' && filesUploaded && (
        <SuiteFiles files={selectedFiles} />
      )}
    </div>
  );
};
