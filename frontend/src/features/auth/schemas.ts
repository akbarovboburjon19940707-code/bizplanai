import { z } from "zod";
import { uz } from "@/messages/uz";
import { isCompletePhone } from "@/shared/lib/phone";

const t = uz.authForms;

const phone = z.string().refine(isCompletePhone, t.phoneIncomplete);

export const loginSchema = z.object({
  phone,
  password: z.string().min(1, t.passwordRequired).max(128),
  totp_code: z
    .string()
    .trim()
    .refine((v) => v === "" || /^\d{6}$/.test(v), t.login.totpFormat),
});
export type LoginValues = z.infer<typeof loginSchema>;

export const registerSchema = z
  .object({
    first_name: z.string().trim().max(100),
    phone,
    password: z.string().min(8, t.passwordMin).max(128),
    password_confirm: z.string(),
  })
  .refine((v) => v.password === v.password_confirm, { path: ["password_confirm"], message: t.passwordMismatch });
export type RegisterValues = z.infer<typeof registerSchema>;

export const resetPhoneSchema = z.object({ phone });
export type ResetPhoneValues = z.infer<typeof resetPhoneSchema>;

export const newPasswordSchema = z
  .object({
    password: z.string().min(8, t.passwordMin).max(128),
    password_confirm: z.string(),
  })
  .refine((v) => v.password === v.password_confirm, { path: ["password_confirm"], message: t.passwordMismatch });
export type NewPasswordValues = z.infer<typeof newPasswordSchema>;
