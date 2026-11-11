// out/ ni Render Static Site kabi beradi: trailing slash, /tolov/* -> /tolov/_/index.html, 404.html.
// Faqat e2e va lokal tekshiruv uchun: `npm run serve:static` (PORT=3000).
import { createReadStream, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";

const ROOT = join(process.cwd(), "out");
const PORT = Number(process.env.PORT || 3000);
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json",
  ".txt": "text/plain; charset=utf-8", ".xml": "application/xml", ".svg": "image/svg+xml", ".png": "image/png",
  ".ico": "image/x-icon", ".woff2": "font/woff2", ".webp": "image/webp" };

function file(path) {
  try {
    const st = statSync(path);
    return st.isDirectory() ? file(join(path, "index.html")) : path;
  } catch {
    return null;
  }
}

createServer((req, res) => {
  let pathname = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (pathname.startsWith("/tolov/") && !pathname.startsWith("/tolov/_/")) pathname = "/tolov/_/index.html";
  const target = normalize(join(ROOT, pathname));
  const found = target.startsWith(ROOT) ? file(target) : null;
  const path = found ?? join(ROOT, "404.html");
  res.writeHead(found ? 200 : 404, { "Content-Type": TYPES[extname(path)] ?? "application/octet-stream" });
  createReadStream(path).pipe(res);
}).listen(PORT, () => console.log(`static: http://localhost:${PORT}`));
