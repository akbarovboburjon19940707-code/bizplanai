import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import { AuthProvider } from "@/features/auth/auth-context";
import { TelegramContextMarker } from "@/features/telegram/telegram-context-marker";
import { SiteFooter } from "@/shared/ui/site-footer";
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
  openGraph: { type: "website", siteName: uz.appName, locale: "uz_UZ", title: uz.appName, description: uz.home.description,
    images: [{ url: "/logo-512.png", width: 512, height: 512, alt: uz.appName }] },
  twitter: { card: "summary" },
  // canonical ataylab bu yerda yo'q: layout'dagi qiymat har sahifaga meros bo'lib, hammasini "/" nusxasi qilardi
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="uz">
      <body className={`${inter.variable} ${outfit.variable} min-h-screen antialiased`}>
        <AuthProvider>
          <TelegramContextMarker />
          <div className="flex min-h-screen flex-col">
            <SiteHeader />
            <main className="flex-1">{children}</main>
            <SiteFooter />
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
