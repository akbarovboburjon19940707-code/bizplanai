import type { FieldValues, Path, UseFormSetError } from "react-hook-form";
import { uz } from "@/messages/uz";
import { ApiError } from "./errors";

type Detail = { field?: unknown; message?: unknown };

/**
 * API xatosini formaga qo'llaydi: `validation_error` dagi `details[].field` ni mos maydonga,
 * qolganini forma darajasidagi xabar sifatida qaytaradi. `fields` - formadagi maydon nomlari.
 */
export function applyApiError<T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  fields: readonly Path<T>[],
): string | null {
  if (!(error instanceof ApiError)) return uz.authForms.genericError;
  if (error.code === "validation_error" && Array.isArray(error.details)) {
    let unmatched = false;
    for (const d of error.details as Detail[]) {
      const field = typeof d.field === "string" ? d.field.split(".").pop() : undefined;
      const message = typeof d.message === "string" ? d.message.replace(/^Value error,\s*/, "") : error.message;
      if (field && (fields as readonly string[]).includes(field)) {
        setError(field as Path<T>, { type: "server", message });
      } else {
        unmatched = true;
      }
    }
    return unmatched ? error.message : null;
  }
  return error.message;
}
