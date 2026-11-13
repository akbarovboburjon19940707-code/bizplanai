"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/auth-context";
import { uz } from "@/messages/uz";
import { cn } from "@/shared/lib/cn";
import { BrandLogo } from "./brand-logo";
import { Button } from "./button";

const nav = uz.navigation;

function NavLink({ href, label, className }: { href: string; label: string; className?: string }) {
  const active = usePathname()?.startsWith(href.replace(/\/$/, "")) ?? false;
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "rounded-control px-3 py-2 text-sm font-semibold transition hover:bg-canvas focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand",
        active ? "text-brand" : "text-ink",
        className,
      )}
    >
      {label}
    </Link>
  );
}

export function SiteHeader() {
  const { status, user, signOut } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  const handleSignOut = async () => {
    await signOut();
    router.push("/");
  };

  // Telegram Mini App o'z sarlavhasiga ega: sayt menyusi kerak emas
  if (pathname?.startsWith("/tg")) return null;

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex shrink-0 items-center gap-3" aria-label={uz.appName}>
          <BrandLogo size={40} className="size-10" />
          <span className="hidden text-lg font-bold tracking-tight text-ink sm:inline">{uz.appName}</span>
        </Link>
        <nav aria-label={nav.menu} className="flex items-center gap-1 sm:gap-2">
          <NavLink href="/katalog/" label={nav.catalog} className="hidden md:inline-flex" />
          <NavLink href="/tariflar/" label={nav.tariffs} className="hidden md:inline-flex" />
          <NavLink href="/#savollar" label={nav.faq} className="hidden lg:inline-flex" />
          <NavLink href="/aloqa/" label={nav.contact} className="hidden lg:inline-flex" />
          <NavLink href="/dashboard/" label={nav.createPlan} className="hidden sm:inline-flex" />
          {status === "loading" ? (
            <span className="h-9 w-24 animate-pulse rounded-control bg-slate-100" aria-label={uz.auth.loading} />
          ) : status === "authenticated" ? (
            <>
              {user?.role === "admin" ? <NavLink href="/admin/" label={nav.admin} /> : null}
              <NavLink href="/kabinet/" label={user?.first_name || nav.account} className="max-w-[10rem] truncate" />
              <Button type="button" variant="outline" size="md" onClick={() => void handleSignOut()}>
                {nav.signOut}
              </Button>
            </>
          ) : (
            <>
              <NavLink href="/kirish/" label={nav.signIn} />
              <Button asChild size="md">
                <Link href="/royxat/">{nav.signUp}</Link>
              </Button>
            </>
          )}
        </nav>
      </div>
      {/* Kichik ekranlar: asosiy bo'limlar header ostida (katta ekranda yuqoridagi menyuda; Aloqa lg dan) */}
      <nav aria-label={nav.menu} className="border-t border-slate-100 lg:hidden">
        <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-2 py-1">
          <NavLink href="/katalog/" label={nav.catalog} className="md:hidden" />
          <NavLink href="/tariflar/" label={nav.tariffs} className="md:hidden" />
          <NavLink href="/dashboard/" label={nav.createPlan} className="sm:hidden" />
          <NavLink href="/aloqa/" label={nav.contact} />
        </div>
      </nav>
    </header>
  );
}
