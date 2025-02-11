import Link from 'next/link';
import { ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ExperimentDetails } from '@/components/details';

export default async function Details({
  params,
}: {
  params: { experimentId: string };
}) {
  const experimentId = params?.experimentId || '';

  return (
    <div>
      <div className='flex justify-between my-2'>
        <h1 className='text-2xl font-bold'>Details for #{experimentId}</h1>
        <div>
          <Button variant='ghost' asChild>
            <Link href='/experiments'>
              <ChevronLeft />
              Go back
            </Link>
          </Button>
        </div>
      </div>
      <div className='container mx-auto mt-4'>
        <ExperimentDetails experimentId={experimentId} />
      </div>
    </div>
  );
}
