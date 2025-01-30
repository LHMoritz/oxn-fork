'use client';
import React from 'react';
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Cable } from "lucide-react";
import { FileUploader } from '../file-upload';

interface StartDialogProps {
  experimentType: string;
  title: string;
}

const StartDialog: React.FC<StartDialogProps> = ({ experimentType, title }) => {
  const allowMultiple = experimentType !== 'single'; //Batch or suite can have multiple file uploads
  return (
    <Dialog>
      <DialogTrigger>
        <div className='flex items-center gap-2 border-collapse border border-black-300 rounded-md py-2 px-4 cursor-pointer bg-black text-white'>
          <Cable size={14} />
          <span className='text-sm'>Start {title}</span>
        </div>
      </DialogTrigger>
      <DialogContent className="max-w-[900px] w-full max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle>Start {title}</DialogTitle>
          <DialogDescription>
            Upload YAML file/s with experiment configurations.
          </DialogDescription>
        </DialogHeader>
        {/* File Upload Process */}
        <FileUploader allowMultiple={allowMultiple} experimentType={experimentType} />
      </DialogContent>
    </Dialog>
  );
};

export default StartDialog;
