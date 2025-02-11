/* eslint-disable  @typescript-eslint/no-explicit-any */
'use client';
import { load as yamlLoad } from 'js-yaml';
import { useEffect, useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Cable, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useApi } from '@/hooks/use-api';
import CodeMirror from '@uiw/react-codemirror';
import { yaml } from '@codemirror/lang-yaml';
import { json } from '@codemirror/lang-json';
import { useTheme } from 'next-themes';

interface SuiteFilesProps {
  files: File[];
}

export const SuiteFiles: React.FC<SuiteFilesProps> = ({ files }) => {
  const [expandedFileIndex, setExpandedFileIndex] = useState<number | null>(
    null
  );
  const [fileContents, setFileContents] = useState<{ [key: number]: string }>(
    {}
  );
  const [fileTypes, setFileTypes] = useState<{
    [key: number]: 'yaml' | 'json' | null;
  }>({});
  const [areFilesCreated, setAreFilesCreated] = useState(false);
  const [experimentIds, setExperimentIds] = useState(null);
  const [parsedExperimentFiles, setParsedExperimentFiles] = useState<any[]>([]);

  const { theme } = useTheme();

  const {
    data: responseAfterCreate,
    loading: loadingOnCreate,
    fetchData: onCreateSuite,
  } = useApi({
    url: '/experiments/suite',
    method: 'POST',
    body: {
      experiments: parsedExperimentFiles,
    },
  });

  const { loading: loadingOnStart, fetchData: onStartSuite } = useApi({
    url: '/experimentsuite/run',
    method: 'POST',
    body: {
      experimentIds: experimentIds,
    },
  });

  useEffect(() => {
    if (responseAfterCreate) {
      const experimentIds =
        responseAfterCreate.map((experiment: any) => experiment.id) || [];
      setExperimentIds(experimentIds);
    }
  }, [responseAfterCreate]);

  useEffect(() => {
    if (parsedExperimentFiles.length > 0) {
      onCreateSuite();
    }
  }, [parsedExperimentFiles]);

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

        if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
          setFileTypes((prev) => ({ ...prev, [index]: 'yaml' }));
        } else if (file.name.endsWith('.json')) {
          setFileTypes((prev) => ({ ...prev, [index]: 'json' }));
        }
      };
      reader.readAsText(file);
    }

    setExpandedFileIndex(index);
  };

  const handleFileCreate = () => {
    const experiments = files.map((file, index) => {
      const content = fileContents[index];
      const type = fileTypes[index];
      let parsed;

      if (type === 'json') {
        try {
          parsed = JSON.parse(content);
        } catch (error) {
          console.error(`Error parsing JSON for file ${file.name}:`, error);
        }
      } else if (type === 'yaml') {
        try {
          parsed = yamlLoad(content);
        } catch (error) {
          console.error(`Error parsing YAML for file ${file.name}:`, error);
        }
      }
      return parsed;
    });

    setParsedExperimentFiles(experiments);
    setAreFilesCreated(true);
  };

  const handleStartExperiment = () => {
    if (experimentIds) onStartSuite();
  };

  return (
    <div className='space-y-4'>
      <h2 className='text-lg font-semibold'>Files Preview</h2>
      <ScrollArea className='h-full w-full border rounded-md p-2'>
        {files.map((file, index) => (
          <div key={index} className='mb-2'>
            <div className='flex justify-between'>
              <div className='flex items-center gap-2'>
                <FileText size={18} />
                {file.name}
              </div>
              <div className='flex gap-2'>
                <Button
                  variant='outline'
                  onClick={() => toggleFileExpansion(index, file)}
                >
                  {expandedFileIndex === index ? (
                    <div className='flex items-center gap-1'>
                      <span>Collapse</span>
                      <ChevronUp size={20} />
                    </div>
                  ) : (
                    <div className='flex items-center gap-1'>
                      <span>Expand</span>
                      <ChevronDown size={20} />
                    </div>
                  )}
                </Button>
              </div>
            </div>

            {expandedFileIndex === index && (
              <div className='p-3 w-[800px]'>
                {fileContents[index] && fileTypes[index] && (
                  <CodeMirror
                    value={fileContents[index]}
                    editable={false}
                    extensions={[fileTypes[index] === 'yaml' ? yaml() : json()]}
                    theme={theme === 'light' ? 'light' : 'dark'}
                  />
                )}
              </div>
            )}
          </div>
        ))}
      </ScrollArea>

      <div className='flex justify-end gap-2 my-4 w-full'>
        <Button
          disabled={areFilesCreated || loadingOnCreate}
          onClick={handleFileCreate}
          variant='outline'
        >
          <Save />
          {areFilesCreated ? 'Files created!' : 'Create files'}
        </Button>

        <Button
          disabled={!areFilesCreated || loadingOnStart}
          onClick={handleStartExperiment}
        >
          <Cable />
          Start Suite
        </Button>
      </div>
    </div>
  );
};
