"""Render blueprint'lari (render.*.yaml) uchun himoya testlari.

Bu yerdagi qoidalar buzilsa xato faqat production'da, yuklama ostida ko'rinadi, shuning uchun CI'da tekshiriladi:
Postgres ulanish byudjeti, production deploy darvozasi va Mini App uchun iframe ruxsati.
"""
from pathlib import Path

import pytest
import yaml

from app.core.config import Settings

ROOT = Path(__file__).resolve().parents[2]
BLUEPRINTS = ["render.staging.yaml", "render.production.yaml"]

# Render Postgres: RAM 8 GB dan kam tariflarda max_connections = 100. 10 tasi superuser, migratsiya va Shell uchun.
PG_MAX_CONNECTIONS = {"basic-256mb": 100, "basic-1gb": 100, "basic-4gb": 100}
PG_RESERVED = 10

pytestmark = pytest.mark.skipif(not (ROOT / BLUEPRINTS[0]).exists(),
                                reason="blueprint'lar repo ildizida (Docker image ichida yo'q)")


def _load(name: str) -> dict:
    return yaml.safe_load((ROOT / name).read_text(encoding="utf-8"))


def _env(service: dict) -> dict[str, str]:
    return {e["key"]: str(e["value"]) for e in service.get("envVars", []) if "key" in e and "value" in e}


def _max_instances(service: dict) -> int:
    if "scaling" in service:
        return int(service["scaling"]["maxInstances"])
    return int(service.get("numInstances", 1))


def _backend_services(bp: dict) -> list[dict]:
    return [s for s in bp["services"] if s.get("runtime") == "docker"]


@pytest.mark.parametrize("name", BLUEPRINTS)
def test_postgres_connection_budget(name):
    bp = _load(name)
    defaults = Settings.model_fields
    total = 0
    for svc in _backend_services(bp):
        env = _env(svc)
        # worker (arq) bitta jarayon; API uvicorn --workers WEB_CONCURRENCY (Dockerfile'da standart 2)
        processes = int(env.get("WEB_CONCURRENCY", 2)) if svc["type"] == "web" else 1
        per_process = (int(env.get("DB_POOL_SIZE", defaults["db_pool_size"].default))
                       + int(env.get("DB_MAX_OVERFLOW", defaults["db_max_overflow"].default)))
        total += _max_instances(svc) * processes * per_process

    (db,) = bp["databases"]
    limit = PG_MAX_CONNECTIONS[db["plan"]] - PG_RESERVED
    assert total <= limit, (
        f"{name}: to'liq kengayganda {total} ta Postgres ulanishi kerak, {db['plan']} da {limit} ta bor. "
        "DB_POOL_SIZE/DB_MAX_OVERFLOW ni kamaytiring, nusxa sonini qisqartiring yoki PgBouncer qo'ying."
    )


def test_production_deploys_only_from_production_branch_after_ci():
    for svc in _load("render.production.yaml")["services"]:
        if svc["type"] == "keyvalue":
            continue
        assert svc.get("branch") == "production", svc["name"]
        assert svc.get("autoDeployTrigger") == "checksPass", svc["name"]


@pytest.mark.parametrize("name", BLUEPRINTS)
def test_static_site_can_be_framed_by_telegram_only(name):
    (web,) = [s for s in _load(name)["services"] if s.get("runtime") == "static"]
    headers = {h["name"]: h["value"] for h in web["headers"]}
    # X-Frame-Options: DENY Telegram Web'dagi Mini App'ni (iframe) bloklaydi; ruxsat faqat frame-ancestors orqali
    assert "X-Frame-Options" not in headers
    directives = dict(d.strip().split(" ", 1) for d in headers["Content-Security-Policy"].split(";") if " " in d.strip())
    assert directives["frame-ancestors"].split() == ["'self'", "https://*.telegram.org"]
