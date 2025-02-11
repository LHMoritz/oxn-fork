import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { experimentType } from '@/types/experiment';
import StartExperimentDialog from './start-dialog';

interface StartExperimentProps {
  experimentType: experimentType;
  title: string;
  icon: React.ReactNode;
  description: string;
  disabled?: boolean;
}

export const StartExperiment: React.FC<StartExperimentProps> = ({
  title,
  icon,
  description,
  experimentType,
  disabled = false,
}) => {
  return (
    <Card className='w-[400px]'>
      <CardHeader>
        <CardTitle className='flex justify-between align-baseline'>
          {title}
          {icon}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardFooter className='flex justify-end py-6'>
        <StartExperimentDialog
          disabled={disabled}
          title={title}
          experimentType={experimentType}
        />
      </CardFooter>
    </Card>
  );
};
