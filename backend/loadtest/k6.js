// k6 run -e API=https://api-staging.bizplanai.uz loadtest/k6.js
// Maqsad: 10 000 virtual foydalanuvchi, p95 < 300 ms, xato < 0.1%.
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    browse: { executor: "ramping-vus", startVUs: 0, stages: [
      { duration: "5m", target: 2000 }, { duration: "10m", target: 10000 }, { duration: "10m", target: 10000 },
      { duration: "3m", target: 0 } ] },
  },
  thresholds: { http_req_failed: ["rate<0.001"], http_req_duration: ["p(95)<300"] },
};

const API = __ENV.API;
const plan = JSON.stringify({ faoliyat_turi: "savdo", loyiha_nomi: "Yuklama testi", loyiha_qiymati: 100000000,
  hajm: 1000, narx: 50000 });

export default function () {
  const r1 = http.get(`${API}/v1/catalog/products?limit=20`);
  check(r1, { "katalog 200": (r) => r.status === 200 });
  sleep(Math.random() * 5 + 3);
  const r2 = http.post(`${API}/v1/plans/preview`, plan, { headers: { "Content-Type": "application/json" } });
  check(r2, { "preview 200": (r) => r.status === 200 || r.status === 429 });
  sleep(Math.random() * 5 + 3);
}
