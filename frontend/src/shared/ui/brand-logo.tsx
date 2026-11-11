import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";

/** bizplanai.uz belgisi ("b", public/logo.png, 160 px). To'liq logotip (yozuvi bilan) public/logo-512.png: ulashish rasmi. */
export function BrandLogo({ size = 40, className }: { size?: number; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- static export: next/image optimizatori yo'q
    <img src="/logo.png" alt={uz.appName} width={size} height={size} decoding="async"
      className={cn("shrink-0 rounded-full", className)} />
  );
}
