import Link from "next/link";
import { uz } from "@/messages/uz";

export default function NotFound() {
  return (
    <section className="mx-auto flex min-h-[60vh] max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
      <p className="text-sm font-bold uppercase tracking-[0.2em] text-brand">404</p>
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-ink">Sahifa topilmadi</h1>
      <p className="mt-3 text-muted">Manzilni tekshiring yoki bosh sahifaga qayting.</p>
      <Link className="mt-7 rounded-control bg-brand px-5 py-3 font-semibold text-white hover:bg-brand-hover" href="/">
        {uz.navigation.home}
      </Link>
    </section>
  );
}
