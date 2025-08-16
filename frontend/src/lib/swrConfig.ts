import useSWR, { SWRConfiguration } from "swr";
import { api } from "./apiClient";

export const defaultSWRConfig: SWRConfiguration = {
  fetcher: (url: string) => api.get(url).then(res => res.data),
  revalidateOnFocus: true,
  shouldRetryOnError: false,
};

export const useApi = (key: string | null) => useSWR(key, defaultSWRConfig.fetcher);
