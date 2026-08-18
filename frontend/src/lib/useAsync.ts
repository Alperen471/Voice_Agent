"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "./api";

interface UseAsyncResult<T> {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
}

/**
 * Ortak veri çekme kalıbı: yükleme/hata/yeniden deneme durumlarını tek yerden yönetir.
 * `loading`, data ve error'dan türetilir — effect içinde senkron setState çağrısı yapılmaz.
 */
export function useAsync<T>(fetcher: () => Promise<T>, deps: unknown[] = []): UseAsyncResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let ignore = false;
    fetcher()
      .then((result) => {
        if (!ignore) setData(result);
      })
      .catch((err: unknown) => {
        if (!ignore) setError(err instanceof ApiError ? err.message : "Beklenmeyen bir hata oluştu.");
      });
    return () => {
      ignore = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadToken]);

  const reload = useCallback(() => {
    setData(null);
    setError(null);
    setReloadToken((t) => t + 1);
  }, []);

  return { data, error, loading: data === null && error === null, reload };
}
