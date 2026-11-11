from sqlalchemy import func, select

from tests.conftest import put_catalog_pdf


async def test_check_catalog_reports_and_hides_products_without_pdf(client, capsys, tmp_path):
    from app.cli import check_catalog
    from app.db.session import sessionmaker
    from app.models import CatalogProduct

    items = (await client.get("/v1/catalog/products", params={"limit": 2})).json()["items"]
    for p in items:
        await put_catalog_pdf(p["id"])

    await check_catalog(hide_missing=False, report_path=str(tmp_path / "r.csv"))
    out = capsys.readouterr().out
    assert "faol rejalar: 269, PDF yo'q: 267" in out
    assert (tmp_path / "r.csv").read_text(encoding="utf-8").count("\n") == 270

    await check_catalog(hide_missing=True, report_path=None)
    async with sessionmaker()() as s:
        active = await s.scalar(select(func.count()).select_from(CatalogProduct).where(CatalogProduct.is_active.is_(True)))
    assert active == 2
    assert (await client.get("/v1/catalog/products")).json()["total"] == 2
