export type experimentType = 'single' | 'batch' | 'suite';
export type experimentStatus = 'PENDING' | 'COMPLETED' | 'FAILED';

export interface Experiments {
  id: string;
  name: string;
  status: string;
  created_at: string;
  started_at: string;
  completed_at: string;
  error_message: string;
}