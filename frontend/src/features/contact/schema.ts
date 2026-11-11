import { z } from "zod";
import { uz } from "@/messages/uz";
import { isCompletePhone } from "@/shared/lib/phone";

const t = uz.contact;
export const TOPICS = ["plan", "payment", "catalog", "partnership", "other"] as const;

export const contactSchema = z.object({
  name: z.string().trim().min(2, t.nameMin).max(100),
  phone: z.string().refine(isCompletePhone, uz.authForms.phoneIncomplete),
  topic: z.enum(TOPICS),
  message: z.string().trim().min(10, t.messageMin).max(2000, t.messageMax),
  website: z.string().max(200), // honeypot: ko'rinmaydi, odam to'ldirmaydi
});
export type ContactValues = z.infer<typeof contactSchema>;
