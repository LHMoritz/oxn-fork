'use client';
import React from 'react';
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
  disabled: boolean;
}

const StartDialog: React.FC<StartDialogProps> = ({ experimentType, title, disabled }) => {
  const allowMultiple = experimentType === 'suite'; //Single and batch have single file upload
  return (
    <Dialog>
      <DialogTrigger disabled={disabled}>
        <div className={`flex items-center gap-2 border-collapse border border-black-300 rounded-md py-2 px-4 text-white ${disabled ? 'bg-slate-400 cursor-not-allowed' : 'bg-black cursor-pointer'}`}>
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
