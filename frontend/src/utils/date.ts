import { format } from 'date-fns';

export const DATE_TIME_LONG_FORMAT = 'yyyy-MM-dd HH:mm:ss';
export const DATE_TIME_SHORT_FORMAT = 'dd MMM HH:mm';
export const DATE_MONTH_FORMAT = 'd MMM yyyy';

export function formatDate(dateString: Date | string, formatType = DATE_TIME_LONG_FORMAT) {
  try {
    const date = new Date(dateString);
    return format(date, formatType);
  } catch (error) {
    console.error('Invalid date:', dateString);
    return null;
  }
};
