"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/shared/lib/cn";

export function CoverImage({ src, title, className, eager }: { src: string; title: string; className?: string; eager?: boolean }) {
  const [failed, setFailed] = useState(false);
  const ref = useRef<HTMLImageElement>(null);

  // Static HTML'dagi rasm React ulanishidan oldin xato bersa, onError o'tkazib yuboriladi: shu yerda tekshiramiz
  useEffect(() => {
    const img = ref.current;
    if (img?.complete && img.naturalWidth === 0) setFailed(true);
  }, []);
  if (!src || failed) {
    return (
      <div className={cn("grid place-items-center bg-gradient-to-br from-slate-900 via-blue-900 to-blue-600", className)} aria-hidden="true">
        <span className="line-clamp-3 px-6 text-center text-sm font-semibold text-white/85">{title}</span>
      </div>
    );
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- static export: next/image optimizatori yo'q
    <img
      ref={ref}
      src={src}
      alt=""
      width={640}
      height={400}
      loading={eager ? "eager" : "lazy"}
      decoding="async"
      onError={() => setFailed(true)}
      className={cn("bg-slate-100 object-cover", className)}
    />
  );
}
