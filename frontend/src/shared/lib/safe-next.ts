/**
 * `?next=` qiymatini faqat sayt ichidagi yo'l bo'lsa qabul qiladi (open redirect himoyasi).
 * "//evil.com", "/\\evil.com", "https://..." va boshqarish belgilari rad etiladi.
 */
export function safeNextPath(raw: string | null | undefined, fallback = "/kabinet/"): string {
  if (!raw || raw.length > 512) return fallback;
  if (!raw.startsWith("/") || raw.startsWith("//") || raw.startsWith("/\\")) return fallback;
  if (/[\u0000-\u001f\\]/.test(raw)) return fallback;
  if (/^\/(kirish|royxat)(\/|$|\?)/.test(raw)) return fallback; // kirish sahifasiga qaytib aylanmasin
  return raw;
}
