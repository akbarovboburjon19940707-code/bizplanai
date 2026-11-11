export const FAST_MS = 3000; // Click/Payme: callback tez keladi
export const SLOW_MS = 15000; // chek tekshirilmoqda (admin qo'lda tasdiqlaydi) yoki tarmoq xatosi

/** Holatga qarab keyingi so'rov kechikishi; 0 = so'ramaslik (yakuniy holat yoki chek kutilmoqda). */
export function pollDelay(status: string, provider: string): number {
  if (status === "reviewing") return SLOW_MS;
  if (status === "pending" && provider !== "manual") return FAST_MS;
  return 0;
}
