'use client';
import { useEffect, useState } from 'react';
import { Cable, Save } from 'lucide-react';
import { Button } from '../../../ui/button';
import CodeMirror from '@uiw/react-codemirror';
import { yaml as yamlFormat } from '@codemirror/lang-yaml';
import { json as jsonFormat } from '@codemirror/lang-json';
import { useApi } from '@/hooks/use-api';
import { useTheme } from 'next-themes';
import yaml from 'js-yaml';

interface SingleFileProps {
  file: File;
}

export const SingleFile: React.FC<SingleFileProps> = ({ file }) => {
  const [editableFile, setEditableFile] = useState<string | null>(null);
  const [fileType, setFileType] = useState<'yaml' | 'json' | null>(null);
  const [isFileCreated, setIsFileCreated] = useState(false);
  const [experimentId, setExperimentId] = useState(null);
  const { theme } = useTheme();

  const parsedConfig =
    fileType === 'yaml'
      ? yaml.load(editableFile || '')
      : JSON.parse(editableFile || '{}');

  const {
    data: responseAfterCreate,
    loading: loadingOnCreate,
    fetchData: onCreateExperiment,
  } = useApi({
    url: `/experiments`,
    method: 'POST',
    body: parsedConfig,
  });

  const { loading: loadingOnStart, fetchData: onStartExperiment } = useApi({
    url: `/experiments/${experimentId}/runsync`,
    method: 'POST',
    body: {
      runs: 1,
      output_formats: ['json'],
    },
  });

  useEffect(() => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setEditableFile(content);

      if (file.name.endsWith('.yaml') || file.name.endsWith('.yml')) {
        setFileType('yaml');
      } else if (file.name.endsWith('.json')) {
        setFileType('json');
      }
    };
    reader.readAsText(file);
  }, [file]);

  useEffect(() => {
    if (responseAfterCreate) setExperimentId(responseAfterCreate.id);
  }, [responseAfterCreate]);

  const handleFileCreate = () => {
    setIsFileCreated(true);
    onCreateExperiment();
  };

  const handleStartExperiment = () => {
    if (experimentId) onStartExperiment();
  };

  const onFileChange = (newFileValue: string) => {
    setEditableFile(newFileValue);
  };

  return (
    <div>
      <div className='mt-4'>
        <h3 className='text-lg font-semibold mb-2'>File Preview:</h3>
        <div className='max-h-[50vh] max-w-[850px] overflow-auto'>
          {editableFile && (
            <CodeMirror
              editable
              value={editableFile}
              extensions={[fileType === 'yaml' ? yamlFormat() : jsonFormat()]}
              theme={theme === 'light' ? 'light' : 'dark'}
              onChange={onFileChange}
            />
          )}
        </div>
      </div>

      <div className='flex justify-end gap-2 my-4 w-full'>
        <Button
          disabled={isFileCreated || loadingOnCreate}
          onClick={handleFileCreate}
          variant='outline'
        >
          <Save />
          {isFileCreated ? 'File created!' : 'Create file'}
        </Button>

        <Button
          disabled={!isFileCreated || loadingOnStart}
          onClick={handleStartExperiment}
        >
          <Cable />
          Start Experiment
        </Button>
      </div>
    </div>
  );
};
