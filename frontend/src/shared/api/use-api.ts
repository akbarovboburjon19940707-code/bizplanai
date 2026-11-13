"use client";

import { useCallback, useEffect, useState } from "react";
import { apiRequest } from "./client";
import { ApiError } from "./errors";

type State<T> = { data: T | null; error: ApiError | null; loading: boolean };

/**
 * Oddiy GET so'rovi: yuklash, xato va qayta yuklash. `path` null bo'lsa so'rov yuborilmaydi.
 * `initial`: build vaqtida olingan ma'lumot (HTML'da darhol ko'rinadi, SEO uchun); baribir yangisi so'raladi.
 */
export function useApi<T>(path: string | null, initial: T | null = null) {
  const [state, setState] = useState<State<T>>({ data: initial, error: null, loading: path !== null });
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!path) return;
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    apiRequest<T>(path)
      .then((data) => active && setState({ data, error: null, loading: false }))
      .catch((e: unknown) => {
        if (!active) return;
        const error = e instanceof ApiError ? e : new ApiError(0, "network_error", "");
        setState((s) => ({ ...s, error, loading: false }));
      });
    return () => {
      active = false;
    };
  }, [path, version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);
  const replace = useCallback((data: T) => setState({ data, error: null, loading: false }), []);
  return { ...state, reload, replace };
}
