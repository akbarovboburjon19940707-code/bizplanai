import type { MetadataRoute } from "next";
import { SITE_URL } from "@/shared/lib/site";

export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    // Shaxsiy va texnik sahifalar indekslanmaydi (staging esa X-Robots-Tag: noindex bilan butunlay yopiq)
    rules: { userAgent: "*", allow: "/", disallow: ["/admin/", "/kabinet/", "/tolov/", "/tg/", "/kirish/", "/royxat/", "/reja/"] },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
