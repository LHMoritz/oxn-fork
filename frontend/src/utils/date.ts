import { format } from 'date-fns';
import { parseISO, formatISO } from "date-fns";


export const DATE_TIME_LONG_FORMAT = 'yyyy-MM-dd HH:mm:ss';
export const DATE_TIME_SHORT_FORMAT = 'dd MMM HH:mm';
export const DATE_MONTH_FORMAT = 'd MMM yyyy';

export function formatDate(dateString: Date | string, formatType = DATE_TIME_LONG_FORMAT) {
  try {
    if (dateString) return format(new Date(dateString), formatType);
    return null;
  } catch (error) {
    console.error('Invalid date:', dateString, error);
    return null;
  }
};

export const formatTimestamp = (timeString?: string | null): string | null => {
  if (!timeString || typeof timeString !== "string") return null;

  try {
    const cleanedTime = timeString.replace(/\.\d+$/, "");
    return formatISO(parseISO(cleanedTime));
  } catch (error) {
    console.error("Invalid timestamp:", timeString, error);
    return null;
  }
};
