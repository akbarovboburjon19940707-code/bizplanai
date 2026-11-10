/** O'zbekiston telefon raqamlari: kiritishda niqob, serverga +998XXXXXXXXX. */

const LOCAL_LENGTH = 9;

/** Kiritilgan matndan 9 xonali mahalliy qismni ajratadi ("+998 90 123..." yoki "90123..." ). */
export function phoneDigits(raw: string): string {
  const trimmed = raw.trim();
  let digits = trimmed.replace(/\D/g, "");
  // "+998..." aniq xalqaro ko'rinish; "998..." esa faqat 9 raqamdan uzun bo'lsa kod deb olinadi
  if (trimmed.startsWith("+998") || (digits.startsWith("998") && digits.length > LOCAL_LENGTH)) {
    digits = digits.slice(3);
  }
  return digits.slice(0, LOCAL_LENGTH);
}

/** Input ichidagi ko'rinish (prefiks alohida): "901234567" -> "90 123 45 67" */
export function formatLocalPhone(raw: string): string {
  const d = phoneDigits(raw);
  return [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)].filter(Boolean).join(" ");
}

/** To'liq ko'rinish: "901234567" -> "+998 90 123 45 67" */
export function formatPhone(raw: string): string {
  const local = formatLocalPhone(raw);
  return local ? `+998 ${local}` : "";
}

export function isCompletePhone(raw: string): boolean {
  return phoneDigits(raw).length === LOCAL_LENGTH;
}

/** Serverga yuboriladigan ko'rinish: +998XXXXXXXXX */
export function toE164(raw: string): string {
  return `+998${phoneDigits(raw)}`;
}
