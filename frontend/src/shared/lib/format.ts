const nf = new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 });

/** 1234567 -> "1 234 567" (bo‘sh joy ajratgich) */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "";
  return nf.format(value).replace(/ | /g, " ");
}

export function formatSom(value: number | null | undefined): string {
  const s = formatNumber(value);
  return s ? `${s} so‘m` : "—";
}

/** "1 234 567,5" -> 1234567.5; bo‘sh bo‘lsa undefined */
export function parseNumber(raw: string): number | undefined {
  const cleaned = raw.replace(/[\s  ]/g, "").replace(",", ".");
  if (!cleaned) return undefined;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : undefined;
}
