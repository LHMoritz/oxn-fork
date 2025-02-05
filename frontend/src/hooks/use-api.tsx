import { useState, useEffect, useCallback, useRef } from "react";
import axios, { AxiosRequestConfig } from "axios";
import { toast } from "react-toastify";

type HttpMethod = "GET" | "POST";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

interface UseApiProps<T> {
  url: string;
  method?: HttpMethod;
  body?: object;
  config?: AxiosRequestConfig;
  manual?: boolean; // If true, GET requests will not run automatically
  showToast?: boolean;
}

export function useApi<T>({
  url,
  method = "GET",
  body = {},
  config = {},
  manual = false, // Default to automatic GET requests
  showToast = true,
}: UseApiProps<T>) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const hasFetched = useRef(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let response;
      if (method === "GET") {
        response = await api.get<T>(url, config);
      } else {
        response = await api.post<T>(url, body, config);
      }
      setData(response.data);

      if (showToast) {
        toast.success('Success!')
      }

      return response.data;
    } catch (err) {
      const errorMessage =
        (err as any)?.response?.data?.message || (err as any)?.message || "An error occurred";
      setError(errorMessage);

      if (showToast) {
        toast.error(errorMessage);
      }

      return null;
    } finally {
      setLoading(false);
    }
  }, [url, method, JSON.stringify(body), JSON.stringify(config)]);

  // Automatically fetch GET requests on mount if `manual` is false
  useEffect(() => {
    if (method === "GET" && !manual && !hasFetched.current) {
      fetchData();
      hasFetched.current = true;
    }
  }, [fetchData, method, manual]);

  return { data, loading, error, fetchData };
}
