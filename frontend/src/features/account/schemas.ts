import { z } from "zod";
import { uz } from "@/messages/uz";

const t = uz.account;

export const profileSchema = z.object({
  first_name: z.string().trim().max(100),
  last_name: z.string().trim().max(100),
  email: z.union([z.literal(""), z.string().trim().email(t.profile.emailInvalid).max(254)]),
});
export type ProfileValues = z.infer<typeof profileSchema>;

export const passwordSchema = z
  .object({
    current_password: z.string().max(128),
    new_password: z.string().min(8, uz.authForms.passwordMin).max(128),
    confirm: z.string(),
  })
  .refine((v) => v.new_password === v.confirm, { path: ["confirm"], message: uz.authForms.passwordMismatch });
export type PasswordValues = z.infer<typeof passwordSchema>;
