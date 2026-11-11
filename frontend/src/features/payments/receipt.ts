const ALLOWED = ["image/jpeg", "image/png", "image/webp", "application/pdf"];
const EXT = /\.(jpe?g|png|webp|pdf)$/i;
export const MAX_RECEIPT_BYTES = 10 * 1024 * 1024;

/** Chek faylini mijoz tomonida tekshiradi (server baribir tekshiradi). Xato bo'lsa sababini qaytaradi. */
export function checkReceipt(file: { name: string; type: string; size: number }): "badType" | "tooLarge" | null {
  if (!(ALLOWED.includes(file.type) || (!file.type && EXT.test(file.name)))) return "badType";
  if (file.size > MAX_RECEIPT_BYTES) return "tooLarge";
  return null;
}
