# BizplanAI

**Bank-ready business plans for Uzbek entrepreneurs in minutes, not weeks.**

Live: **[bizplanai.uz](https://bizplanai.uz)** · Telegram Mini App · Uzbek interface

Every bank loan in Uzbekistan starts with a business plan in the bank's own format: a multi-year cash flow, a loan schedule, NPV, IRR and payback. Farmers, bakers and young founders usually pay a consultant and wait for weeks. BizplanAI turns one simple form into a complete, bank-format package.

## What it does

1. **Enter your data** in a 5-step wizard: project, financing, products and costs, staff, result.
2. **See the result for free.** NPV, IRR, payback, discounted payback, PI, DSCR, break-even and yearly tables are recalculated on screen as you type, for a 1–10 year horizon equal to the loan term.
3. **Pay and download.** Pay with Click or Payme and get a **Word** business plan (bank template), an **Excel** financial model and a **PDF** in seconds. Documents are saved in your cabinet.

Also: a catalog of 260+ ready-made business plans in 6 sectors, and subscriptions for consultants.

## Architecture

```
Next.js (static, CDN) ──┐
Telegram Mini App ──────┼──> FastAPI (stateless API) ──> Postgres
                        │          │
                        │          └──> Redis queue ──> arq worker
                        │                                 ├─ financial engine (NPV, IRR, DSCR, schedules)
                        │                                 ├─ Word / Excel / PDF generation
                        │                                 └─ AI-written sections (rolling out)
                        └──────────── Cloudflare R2 (private, 10-minute signed links)
```

- **backend/**: FastAPI, SQLAlchemy + Alembic, arq workers, financial engine, document templates, Click/Payme payments.
- **frontend/**: Next.js static export, also served as a Telegram Mini App.
- Designed for 10,000 concurrent users: the API is stateless, and heavy work runs in the queue.

## Quality

- 125+ backend tests (pytest) and 31 end-to-end tests (Playwright), run in GitHub Actions CI.
- Admin panel protected with 2FA (TOTP), login lockout and signed download links.

## Run locally

See [`backend/README.md`](backend/README.md) for the API and worker, and [`docs/DEPLOY.md`](docs/DEPLOY.md) for deployment on Render.

## Team

Namangan State Technical University, Uzbekistan.

| Name | Role |
|---|---|
| Boburjon Akbarov | Founder & CEO, AI engineer. Writing business plans since 2018: 1,000+ plans, 95% received a positive bank decision |
| Umidjon Sultonboyev | Product manager |
| Zilola G'apporova | Designer |
| Avazbek Ibrohimov | Mobile developer |
| Toxirjon Maxmudov | Data engineer |

Applicant of the **President Tech Award 2026**.

## History

The first version ([uzbiznesss_site](https://github.com/akbarovboburjon19940707-code/uzbiznesss_site), Flask) went live on 2 September 2026. In November 2026 the platform was rebuilt from scratch as BizplanAI; users, subscriptions and purchases were migrated from the first version.

## License

© 2026 BizplanAI. All rights reserved. The source code is published for review only; copying or reuse requires written permission.
