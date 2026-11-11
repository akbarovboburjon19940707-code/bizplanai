// Build vaqtidagi API ma'lumoti (katalog, tariflar) har build'da yangidan olinsin: Next `force-cache` fetch javoblarini
// .next/cache/fetch-cache da saqlaydi va CI/Render build keshi bilan keyingi build'ga eski narx/limit o'tib ketardi.
import { rmSync } from "node:fs";

rmSync(new URL("../.next/cache/fetch-cache", import.meta.url), { recursive: true, force: true });
