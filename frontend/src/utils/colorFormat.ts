import { STATUS } from "@/types";

export const getBadgeVariant = (status: string) => {

  if (status === STATUS.FINISHED || status === STATUS.COMPLETED)
    return "default";
  else if (status === STATUS.NOT_STARTED)
    return "outline";
  else if (status === STATUS.IN_PROGRESS)
    return "secondary";
  else
    return "destructive";
}