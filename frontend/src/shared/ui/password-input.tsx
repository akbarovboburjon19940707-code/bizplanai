"use client";

import { forwardRef, useState, type InputHTMLAttributes } from "react";
import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";
import { inputClass } from "./form-field";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type">;

/** Parol maydoni, ko'rsatish/yashirish tugmasi bilan. */
export const PasswordInput = forwardRef<HTMLInputElement, Props>(function PasswordInput({ className, ...props }, ref) {
  const [visible, setVisible] = useState(false);
  const t = uz.authForms;
  return (
    <div className="relative">
      <input ref={ref} type={visible ? "text" : "password"} className={cn(inputClass, "pr-20", className)} {...props} />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-pressed={visible}
        aria-label={visible ? t.hidePassword : t.showPassword}
        className="absolute inset-y-1 right-1 rounded-md px-3 text-xs font-semibold text-muted hover:bg-canvas hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
      >
        {visible ? t.hideShort : t.showShort}
      </button>
    </div>
  );
});
