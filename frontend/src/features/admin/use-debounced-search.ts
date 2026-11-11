"use client";

import { useEffect, useState } from "react";

/** Qidiruv maydoni: yozish to'xtagach (350 ms) qiymat qaytadi. */
export function useDebouncedSearch(ms = 350) {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(input.trim()), ms);
    return () => window.clearTimeout(timer);
  }, [input, ms]);
  return { input, setInput, query };
}
