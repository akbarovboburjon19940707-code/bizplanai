"use client";

import { forwardRef, type InputHTMLAttributes } from "react";
import { cn } from "@/shared/lib/cn";
import { formatLocalPhone } from "@/shared/lib/phone";
import { inputClass } from "./form-field";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "value" | "onChange" | "type"> & {
  value: string;
  onChange: (value: string) => void;
};

/** `+998` o'zgarmas prefiks, maydonda "90 123 45 67" niqobi. Qiymat: niqoblangan mahalliy qism. */
export const PhoneInput = forwardRef<HTMLInputElement, Props>(function PhoneInput(
  { value, onChange, className, ...props },
  ref,
) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-sm font-medium text-muted">
        +998
      </span>
      <input
        ref={ref}
        type="tel"
        inputMode="numeric"
        autoComplete="tel-national"
        placeholder="90 123 45 67"
        className={cn(inputClass, "pl-14 tabular-nums", className)}
        value={value}
        onChange={(e) => onChange(formatLocalPhone(e.target.value))}
        {...props}
      />
    </div>
  );
});
