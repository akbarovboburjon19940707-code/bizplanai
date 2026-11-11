import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import { AuthProvider } from "@/features/auth/auth-context";
import { SiteHeader } from "@/shared/ui/site-header";
import { uz } from "@/messages/uz";
import { SITE_URL } from "@/shared/lib/site";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "latin-ext"], variable: "--font-inter", display: "swap" });
const outfit = Outfit({ subsets: ["latin", "latin-ext"], variable: "--font-outfit", display: "swap" });

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: `${uz.appName}: ${uz.home.eyebrow.toLowerCase()}`,
  description: uz.home.description,
  openGraph: { type: "website", siteName: uz.appName, locale: "uz_UZ", title: uz.appName, description: uz.home.description },
  twitter: { card: "summary" },
  alternates: { canonical: "/" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="uz">
      <body className={`${inter.variable} ${outfit.variable} min-h-screen antialiased`}>
        <AuthProvider>
          <div className="flex min-h-screen flex-col">
            <SiteHeader />
            <main className="flex-1">{children}</main>
            <footer className="border-t border-slate-200 bg-white">
              <div className="mx-auto max-w-7xl px-4 py-6 text-sm text-muted sm:px-6 lg:px-8">{uz.footer}</div>
            </footer>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
