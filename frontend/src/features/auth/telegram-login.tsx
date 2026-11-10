"use client";

import { uz } from "@/messages/uz";
import { Button } from "@/shared/ui/button";
import { FormAlert } from "@/shared/ui/form-field";
import { useTelegramLogin } from "./use-telegram-login";

const t = uz.authForms.telegram;

function TelegramIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="size-5 fill-current">
      <path d="M21.9 4.3 18.7 19.4c-.2 1.1-.9 1.3-1.8.8l-4.9-3.6-2.4 2.3c-.3.3-.5.5-1 .5l.4-5 9.1-8.2c.4-.4-.1-.6-.6-.2L6.2 13 1.4 11.5c-1-.3-1.1-1 .2-1.5L20.4 2.9c.9-.3 1.7.2 1.5 1.4Z" />
    </svg>
  );
}

/** "Telegram orqali kirish": botni ochadi va tasdiqlanishini kutadi. */
export function TelegramLogin() {
  const { state, start, cancel } = useTelegramLogin();

  if (state.phase === "waiting") {
    return (
      <div className="flex flex-col gap-3 rounded-control border border-blue-100 bg-blue-50 p-4" aria-live="polite">
        <p className="text-sm text-blue-900">{t.waiting}</p>
        <div className="flex flex-wrap items-center gap-3">
          <Button asChild size="md">
            <a href={state.botUrl} target="_blank" rel="noopener noreferrer">
              <TelegramIcon />
              {t.openBot}
            </a>
          </Button>
          <Button type="button" variant="ghost" onClick={cancel}>
            {t.cancel}
          </Button>
          <span className="ml-auto size-4 animate-spin rounded-full border-2 border-brand border-t-transparent" aria-hidden="true" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {state.phase === "expired" ? <FormAlert tone="info">{t.expired}</FormAlert> : null}
      {state.phase === "error" ? <FormAlert>{state.message || t.unavailable}</FormAlert> : null}
      <Button
        type="button"
        variant="outline"
        size="lg"
        onClick={() => void start()}
        disabled={state.phase === "preparing"}
        className="text-[#229ED9]"
      >
        <TelegramIcon />
        <span className="text-ink">{state.phase === "preparing" ? t.preparing : t.button}</span>
      </Button>
    </div>
  );
}
