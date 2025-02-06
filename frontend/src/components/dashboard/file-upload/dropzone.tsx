'use client';
import { useRef } from "react";
import { File } from "lucide-react";
import { Input } from "@/components/ui/input";

interface DropzoneProps {
  onFileSelect: (files: File[] | File) => void;
  filesAccepted: string[];
  allowMultiple?: boolean;
};

export default function Dropzone({ onFileSelect, filesAccepted, allowMultiple = false }: DropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = filesAccepted.map((ext) => ext.trim().toLowerCase());

  const isValidFileType = (fileName: string) => {
    return allowedExtensions.some((ext) => fileName.toLowerCase().endsWith(ext));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target as HTMLInputElement;
    if (input.files) {
      const files = Array.from(input.files).filter(file => isValidFileType(file.name));
      if (files.length > 0) {
        onFileSelect(allowMultiple ? files : files[0]);
      }
    }
  };

  // Actions on dropzone component
  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    const files = Array.from(e.dataTransfer.files).filter(file => isValidFileType(file.name));
    if (files.length > 0) {
      onFileSelect(allowMultiple ? files : files[0]);
    }
  };

  return (
    <div>
      <div
        className="border-2 border-dashed border-gray-200 rounded-lg flex flex-col gap-1 p-6 items-center cursor-pointer"
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onClick={handleClick}
      >
        <File size={50} />
        <span className="text-sm font-medium text-gray-500">
          Drag and drop or click to browse
        </span>
        <span className="text-xs text-gray-500">
          Allowed files: {allowedExtensions.join(", ")}
        </span>

      </div>

      {/* Hidden Input */}
      <Input
        id="file"
        ref={inputRef}
        type="file"
        multiple={allowMultiple}
        accept={filesAccepted.join(",")}
        onChange={handleFileChange}
        className="hidden"
      />
    </div>
  );
}
