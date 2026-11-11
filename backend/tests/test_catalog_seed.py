import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "catalog.json"


async def test_every_category_gets_its_products(client):
    """catalog.json dagi kategoriya sonlari API bilan bir xil (Transport / Lizing -> transport)."""
    catalog = json.loads(DATA.read_text(encoding="utf-8"))
    expected = {c["key"]: c["count"] for c in catalog["categories"]}
    got = {c["key"]: c["count"] for c in (await client.get("/v1/catalog/categories")).json()}
    assert got == expected
    r = await client.get("/v1/catalog/products", params={"category": "transport", "limit": 100})
    assert r.json()["total"] == 9


def test_migration_0003_moves_misplaced_transport_rows(tmp_path):
    """Eski seed bilan noto'g'ri yozilgan bazada 0003 faqat xizmatlar'dagi transport qatorlarini ko'chiradi."""
    db = tmp_path / "m.db"
    env = {**os.environ, "APP_ENV": "test", "DATABASE_URL": f"sqlite+aiosqlite:///{db}"}
    root = Path(__file__).resolve().parents[1]

    def alembic(*args: str) -> None:
        subprocess.run([sys.executable, "-m", "alembic", *args], cwd=root, env=env, check=True, capture_output=True)

    def run(sql: str, params: tuple = ()) -> list:
        with sqlite3.connect(db) as c:
            return c.execute(sql, params).fetchall()

    alembic("upgrade", "0002")
    subprocess.run([sys.executable, "-m", "app.cli", "seed"], cwd=root, env=env, check=True, capture_output=True)
    # Eski seed holatini qayta yaratamiz: 9 ta transport -> xizmatlar, bittasini admin boshqa joyga ko'chirgan
    run("UPDATE catalog_products SET category_key='xizmatlar' WHERE category_key='transport'")
    run("UPDATE catalog_products SET category_key='savdo' WHERE id='howo-transport-lizing'")

    alembic("upgrade", "head")
    assert run("SELECT count(*) FROM catalog_products WHERE category_key='transport'")[0][0] == 8
    assert run("SELECT category_key FROM catalog_products WHERE id='howo-transport-lizing'")[0][0] == "savdo"

    alembic("downgrade", "0002")
    assert run("SELECT count(*) FROM catalog_products WHERE category_key='transport'")[0][0] == 0
