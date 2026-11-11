"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";
import { formatSom } from "@/shared/lib/format";
import { useAssistant, type ChatItem } from "./use-assistant";

const t = uz.assistant;

function ChatIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true" className={className}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 10h8M8 14h5m-9 6 2.4-3.2A8 8 0 1 1 20 12a8 8 0 0 1-8 8H4Z" />
    </svg>
  );
}

function Bubble({ item, onNavigate }: { item: ChatItem; onNavigate: () => void }) {
  const mine = item.role === "user";
  return (
    <li className={cn("flex flex-col gap-2", mine ? "items-end" : "items-start")}>
      <p className={cn("max-w-[85%] whitespace-pre-wrap break-words rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
        mine ? "rounded-br-md bg-brand text-white" : "rounded-bl-md border border-border bg-white text-ink")}>
        {item.content}
      </p>
      {item.products?.length ? (
        <div className="w-full max-w-[85%]">
          <p className="mb-1 text-xs font-semibold text-muted">{t.products}</p>
          <ul className="flex flex-col gap-1.5">
            {item.products.map((p) => (
              <li key={p.id}>
                <Link href={`/katalog/${encodeURIComponent(p.slug)}/`} onClick={onNavigate}
                  className="flex items-center justify-between gap-3 rounded-control border border-border bg-white px-3 py-2 text-sm transition hover:border-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
                  <span className="line-clamp-2 font-medium text-ink">{p.title}</span>
                  <span className="shrink-0 tabular-nums text-muted">{formatSom(p.price_som)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {item.handoff ? (
        <Link href="/aloqa/" onClick={onNavigate}
          className="rounded-full border border-brand px-3.5 py-1.5 text-sm font-semibold text-brand transition hover:bg-blue-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
          {t.contactCta} →
        </Link>
      ) : null}
    </li>
  );
}

/** Saytning pastki o'ng burchagidagi yordamchi. Mini App (/tg) va admin panelda ko'rsatilmaydi. */
export function ChatWidget() {
  const pathname = usePathname() ?? "";
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const { items, busy, error, send, reset } = useAssistant();
  const listRef = useRef<HTMLUListElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [items, busy, open]);

  useEffect(() => {
    if (!open) return;
    inputRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  if (pathname.startsWith("/tg") || pathname.startsWith("/admin")) return null;

  const submit = () => {
    if (!text.trim() || busy) return;
    void send(text);
    setText("");
  };

  return (
    <>
      {open ? (
        <section role="dialog" aria-label={t.title}
          className="fixed inset-x-2 bottom-2 z-40 flex h-[min(80vh,640px)] flex-col overflow-hidden rounded-card border border-border bg-canvas shadow-2xl sm:inset-x-auto sm:bottom-5 sm:right-5 sm:w-[400px]">
          <header className="flex items-start justify-between gap-3 border-b border-border bg-white px-4 py-3">
            <div>
              <h2 className="font-[var(--font-outfit)] text-base font-bold text-ink">{t.title}</h2>
              <p className="text-xs text-muted">{t.subtitle}</p>
            </div>
            <div className="flex shrink-0 items-center gap-1">
              {items.length ? (
                <button type="button" onClick={reset}
                  className="rounded-control px-2 py-1 text-xs font-semibold text-muted hover:bg-canvas hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
                  {t.reset}
                </button>
              ) : null}
              <button type="button" aria-label={t.close} onClick={() => { setOpen(false); buttonRef.current?.focus(); }}
                className="grid size-8 place-items-center rounded-control text-muted hover:bg-canvas hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
                <svg viewBox="0 0 24 24" className="size-5" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true"><path d="M6 6l12 12M18 6 6 18" /></svg>
              </button>
            </div>
          </header>
          <ul ref={listRef} className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 py-4" aria-live="polite">
            <li className="flex flex-col items-start gap-2">
              <p className="max-w-[85%] rounded-2xl rounded-bl-md border border-border bg-white px-3.5 py-2.5 text-sm leading-relaxed text-ink">{t.greeting}</p>
              {items.length === 0 ? (
                <div className="flex flex-wrap gap-2">
                  {t.suggestions.map((s) => (
                    <button key={s} type="button" onClick={() => void send(s)} disabled={busy}
                      className="rounded-full border border-border bg-white px-3 py-1.5 text-left text-xs font-semibold text-ink transition hover:border-brand hover:text-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
                      {s}
                    </button>
                  ))}
                </div>
              ) : null}
            </li>
            {items.map((item, i) => <Bubble key={i} item={item} onNavigate={() => setOpen(false)} />)}
            {busy ? <li className="text-xs text-muted" role="status">{t.typing}</li> : null}
            {error ? <li role="alert" className="rounded-control border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</li> : null}
          </ul>
          <form className="border-t border-border bg-white p-3" onSubmit={(e) => { e.preventDefault(); submit(); }}>
            <div className="flex items-end gap-2">
              <label htmlFor="assistant-input" className="sr-only">{t.placeholder}</label>
              <textarea id="assistant-input" ref={inputRef} rows={1} maxLength={1000} value={text} placeholder={t.placeholder}
                onChange={(e) => setText(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(); } }}
                className="max-h-32 min-h-11 flex-1 resize-none rounded-control border border-border bg-white px-3 py-2.5 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-blue-100" />
              <button type="submit" disabled={busy || !text.trim()} aria-label={t.send}
                className="grid size-11 shrink-0 place-items-center rounded-control bg-brand text-white transition hover:bg-brand-hover disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2">
                <svg viewBox="0 0 24 24" className="size-5" fill="currentColor" aria-hidden="true"><path d="M3.4 20.4 21 12 3.4 3.6 3.4 10.1 15 12 3.4 13.9Z" /></svg>
              </button>
            </div>
            <p className="mt-2 text-[11px] text-muted">{t.disclaimer}</p>
          </form>
        </section>
      ) : null}
      <button ref={buttonRef} type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open}
        className={cn("fixed bottom-4 right-4 z-30 flex items-center gap-2 rounded-full bg-brand px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-brand-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 sm:bottom-5 sm:right-5",
          open && "hidden")}>
        <ChatIcon className="size-5" />
        {t.open}
      </button>
    </>
  );
}
