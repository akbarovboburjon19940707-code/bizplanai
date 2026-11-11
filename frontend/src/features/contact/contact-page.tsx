import { uz } from "@/messages/uz";
import { CONTACTS } from "@/shared/config/contacts";
import { ContactForm } from "./contact-form";

const t = uz.contact;

function Channel({ label, value, href, external }: { label: string; value: string; href: string; external?: boolean }) {
  return (
    <li>
      <a
        href={href}
        {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
        className="flex flex-col rounded-control border border-border bg-white px-4 py-3 transition hover:border-brand hover:shadow-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand"
      >
        <span className="text-xs font-medium text-muted">{label}</span>
        <span className="mt-0.5 font-semibold text-ink">{value}</span>
      </a>
    </li>
  );
}

/** /aloqa: aloqa usullari (statik, CDN'dan) va murojaat formasi. */
export function ContactPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14 lg:px-8">
      <header className="max-w-2xl">
        <h1 className="font-[var(--font-outfit)] text-3xl font-bold tracking-tight text-ink sm:text-4xl">{t.title}</h1>
        <p className="mt-3 text-base text-muted">{t.subtitle}</p>
      </header>
      <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)]">
        <aside className="flex flex-col gap-6">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">{t.channelsTitle}</h2>
            <ul className="mt-3 flex flex-col gap-2">
              <Channel label={t.phone} value={CONTACTS.phone.display} href={CONTACTS.phone.href} />
              <Channel label={t.telegram} value={CONTACTS.telegram.display} href={CONTACTS.telegram.href} external />
              <Channel label={t.email} value={CONTACTS.email.display} href={CONTACTS.email.href} />
            </ul>
          </div>
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">{t.socialsTitle}</h2>
            <ul className="mt-3 flex flex-wrap gap-2">
              {CONTACTS.socials.map((s) => (
                <li key={s.href}>
                  <a href={s.href} target="_blank" rel="noopener noreferrer"
                    className="inline-flex rounded-full border border-border bg-white px-4 py-2 text-sm font-semibold text-ink transition hover:border-brand hover:text-brand focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand">
                    {s.name}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>
        <div className="rounded-card border border-border bg-white p-5 shadow-soft sm:p-7">
          <h2 className="font-[var(--font-outfit)] text-xl font-bold text-ink">{t.formTitle}</h2>
          <div className="relative mt-5">
            <ContactForm />
          </div>
        </div>
      </div>
    </section>
  );
}
