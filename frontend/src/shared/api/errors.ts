export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, code: string, message: string, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function toApiError(response: Response): Promise<ApiError> {
  let body: ApiErrorBody = {};
  try {
    body = (await response.clone().json()) as ApiErrorBody;
  } catch {
    // Keep a safe generic message if the server did not return JSON.
  }
  return new ApiError(
    response.status,
    body.error?.code ?? "request_failed",
    body.error?.message ?? "So‘rovni bajarib bo‘lmadi. Qayta urinib ko‘ring.",
    body.error?.details,
  );
}
