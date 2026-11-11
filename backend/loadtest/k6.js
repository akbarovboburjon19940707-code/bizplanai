// BizplanAI yuklama testi (k6). Yo'riqnoma: loadtest/README.md
//   k6 run -e API=https://api-yangi.bizplanai.uz -e TOKEN=<LOADTEST_TOKEN> -e PROFILE=smoke loadtest/k6.js
// PROFILE: smoke (tekshiruv) | capacity (bitta nusxa sig'imi) | target (10 000 VU, faqat production o'lchamida)
import http from "k6/http";
import { check, group, sleep } from "k6";
import { Trend } from "k6/metrics";

const API = (__ENV.API || "").replace(/\/$/, "");
const PROFILE = __ENV.PROFILE || "smoke";
if (!API) throw new Error("API berilmagan: -e API=https://api-yangi.bizplanai.uz");
if (/\/\/api\.bizplanai\.uz/.test(API) && __ENV.ALLOW_PROD !== "1") {
  throw new Error("Production API: haqiqiy foydalanuvchilarga ta'sir qiladi. Ataylab bo'lsa -e ALLOW_PROD=1");
}

// Staging'da LOADTEST_TOKEN bilan IP rate limit o'chadi (hamma so'rov bitta kompyuterdan ketadi)
const HEADERS = { "Content-Type": "application/json", ...(__ENV.TOKEN ? { "X-Loadtest-Token": __ENV.TOKEN } : {}) };
http.setResponseCallback(http.expectedStatuses(200, 201, 202, 204));

const PROFILES = {
  smoke: { browse: [{ duration: "30s", target: 5 }, { duration: "1m", target: 5 }], planRate: 2 },
  // Bitta API nusxasining "tizza"sini topish: p95 qaysi bosqichda 300 ms dan oshadi
  capacity: { browse: [50, 100, 200, 400, 800].flatMap((t) => [{ duration: "1m", target: t }, { duration: "2m", target: t }]), planRate: 6 },
  // Maqsad (CLAUDE.md): 10 000 faol foydalanuvchi. Faqat production o'lchamidagi muhitda (8 API / 6 worker)
  target: { browse: [{ duration: "5m", target: 2000 }, { duration: "10m", target: 10000 }, { duration: "10m", target: 10000 }, { duration: "3m", target: 0 }], planRate: 30 },
};
const P = PROFILES[PROFILE];
if (!P) throw new Error(`PROFILE noma'lum: ${PROFILE}`);
const totalSeconds = P.browse.reduce((s, st) => s + parseInt(st.duration, 10) * (st.duration.endsWith("m") ? 60 : 1), 0);

export const options = {
  scenarios: {
    browse: { executor: "ramping-vus", startVUs: 0, stages: P.browse, exec: "browse" },
    // Reja yaratish: daqiqasiga planRate ta, navbatda kutish vaqti o'lchanadi
    plans: { executor: "constant-arrival-rate", rate: P.planRate, timeUnit: "1m", duration: `${totalSeconds}s`,
      preAllocatedVUs: 5, maxVUs: 50, exec: "createPlan" },
  },
  thresholds: {
    http_req_failed: ["rate<0.001"],
    "http_req_duration{kind:read}": ["p(95)<300"],
    "http_req_duration{kind:preview}": ["p(95)<800"], // hisob-kitob: CPU og'ir, alohida chegara
    plan_ready_ms: ["p(95)<30000"],                    // navbat + generatsiya (AI o'chiq bo'lsa)
  },
};

const planReady = new Trend("plan_ready_ms", true);
const PLAN = {
  faoliyat_turi: "savdo", loyiha_nomi: "Yuklama testi do'koni", loyiha_qiymati: 150000000, oz_mablag: 50000000,
  kredit: 100000000, foiz: 22, muddat: 36, imtiyoz: 6, hajm: 12000, narx: 45000, xomashyo_narx: 32000,
  direktor: 1, rahbar_oylik: 5000000, xodim: 3, ishchi_oylik: 3000000,
};

// Har VU o'z foydalanuvchisi bilan (bepul tarif: kuniga 3 reja, shuning uchun reja yaratuvchilar ko'p)
function signUp(tag) {
  const phone = `+99893${String(Math.floor(Math.random() * 1e7)).padStart(7, "0")}`;
  const r = http.post(`${API}/v1/auth/register`, JSON.stringify({ phone, password: "k6-yuklama-123", first_name: tag }),
    { headers: HEADERS, tags: { kind: "auth" }, responseCallback: http.expectedStatuses(201, 409) });
  return r.status === 201 ? r.json("access_token") : null;
}

export function setup() {
  const r = http.get(`${API}/v1/catalog/products?limit=100`, { headers: HEADERS, tags: { kind: "read" } });
  check(r, { "katalog ochiq": (x) => x.status === 200 });
  const slugs = r.json("items").map((p) => p.id);
  if (!slugs.length) throw new Error("Katalog bo'sh");
  return { ids: slugs };
}

export function browse(data) {
  const read = { headers: HEADERS, tags: { kind: "read" } };
  group("katalog", () => {
    const page = Math.floor(Math.random() * 10);
    check(http.get(`${API}/v1/catalog/products?limit=24&offset=${page * 24}`, read), { "katalog 200": (r) => r.status === 200 });
    check(http.get(`${API}/v1/catalog/categories`, read), { "kategoriyalar 200": (r) => r.status === 200 });
    const id = data.ids[Math.floor(Math.random() * data.ids.length)];
    check(http.get(`${API}/v1/catalog/products/${id}`, read), { "reja 200": (r) => r.status === 200 });
    http.get(`${API}/v1/tariffs`, read);
  });
  sleep(Math.random() * 3 + 2);
  group("preview (forma to'ldirish)", () => {
    for (let i = 0; i < 3; i++) { // 500 ms debounce bilan yozish: bir necha so'rov
      const body = JSON.stringify({ ...PLAN, narx: PLAN.narx + i * 1000 });
      check(http.post(`${API}/v1/plans/preview`, body, { headers: HEADERS, tags: { kind: "preview" } }),
        { "preview 200": (r) => r.status === 200 });
      sleep(1);
    }
  });
  if (Math.random() < 0.1) { // har 10-chi tashrif: ro'yxat va kabinet
    group("kabinet", () => {
      const token = signUp("k6");
      if (!token) return;
      const auth = { headers: { ...HEADERS, Authorization: `Bearer ${token}` }, tags: { kind: "read" } };
      check(http.get(`${API}/v1/me`, auth), { "me 200": (r) => r.status === 200 });
      http.get(`${API}/v1/plans?limit=10`, auth);
    });
  }
  sleep(Math.random() * 5 + 3);
}

export function createPlan() {
  const token = signUp("k6-reja");
  if (!token) return;
  const auth = { headers: { ...HEADERS, Authorization: `Bearer ${token}` }, tags: { kind: "plan" } };
  const started = Date.now();
  const r = http.post(`${API}/v1/plans`, JSON.stringify({ input: PLAN, use_ai: false }), auth);
  if (!check(r, { "reja 202": (x) => x.status === 202 })) return;
  const id = r.json("id");
  for (let i = 0; i < 60; i++) { // 2 s oraliq, ko'pi bilan 120 s
    sleep(2);
    const s = http.get(`${API}/v1/plans/${id}`, auth).json("status");
    if (s === "done" || s === "failed") {
      check(s, { "reja tayyor": (x) => x === "done" });
      planReady.add(Date.now() - started);
      return;
    }
  }
  check(null, { "reja 120 s ichida tayyor": () => false });
}
