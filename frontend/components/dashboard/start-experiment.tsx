'use client'
import React from "react"
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
import FileUploader from "../file-upload/file-uploader";

export default function StartExperimentDialog() {

  const [isOpen, setIsOpen] = React.useState(false);
  const [isStartDisabled, setIsStartDisabled] = React.useState(false);

  const handleDialogClose = () => setIsOpen(false);
  const disableStartButton = () => setIsStartDisabled(true);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="default" disabled={isStartDisabled}>
          <Cable />
          {isStartDisabled ? 'Experiment under processing...' : 'Start new experiment'}
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[900px] w-full max-h-[90vh] overflow-auto">
        <DialogHeader>
          <DialogTitle>Start new experiment</DialogTitle>
          <DialogDescription>
            Upload a YAML file with experiment configurations.
          </DialogDescription>
        </DialogHeader>
        {/* File Upload Process */}
        <FileUploader disableStartButton={disableStartButton} handleDialogClose={handleDialogClose} />
      </DialogContent>
    </Dialog>
  );
}
