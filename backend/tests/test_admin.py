from sqlalchemy import select

from tests.conftest import auth, register


async def _admin_headers() -> dict:
    from app.cli import create_admin
    from app.core.security import create_access_token
    from app.db.session import sessionmaker
    from app.models import User

    await create_admin("+998909998877", "juda-kuchli-parol-123")
    async with sessionmaker()() as s:
        admin = (await s.scalars(select(User).where(User.role == "admin"))).one()
    return auth(create_access_token(admin.id, "admin"))


async def test_payment_queue_shows_who_paid(client):
    token = await register(client, phone="+998935554433")
    await client.patch("/v1/me", json={"first_name": "Vali", "last_name": "Karimov"}, headers=auth(token))
    await client.post("/v1/payments", json={"kind": "plan_credit", "provider": "manual"}, headers=auth(token))

    queue = (await client.get("/v1/admin/payments", headers=await _admin_headers())).json()
    assert queue[0]["user_phone"] == "+998935554433" and queue[0]["user_name"] == "Vali Karimov"
    assert queue[0]["has_receipt"] is False


async def test_admin_catalog_lists_hidden_products_and_can_restore_them(client):
    h = await _admin_headers()
    page = (await client.get("/v1/admin/catalog/products", params={"limit": 1}, headers=h)).json()
    assert page["total"] == 269 and page["items"][0]["is_active"] is True
    pid = page["items"][0]["id"]

    hidden = await client.patch(f"/v1/admin/catalog/products/{pid}", json={"is_active": False, "price_som": 33000}, headers=h)
    assert hidden.json()["is_active"] is False and hidden.json()["price_som"] == 33000
    assert (await client.get(f"/v1/catalog/products/{pid}")).status_code == 404  # ommaviy katalogda yo'q

    only_hidden = (await client.get("/v1/admin/catalog/products", params={"active": False}, headers=h)).json()
    assert [p["id"] for p in only_hidden["items"]] == [pid]
    no_file = await client.patch(f"/v1/admin/catalog/products/{pid}", json={"is_active": True}, headers=h)
    assert no_file.status_code == 409 and no_file.json()["error"]["code"] == "file_missing"  # faylsiz sotuv yo'q
    from tests.conftest import put_catalog_pdf
    await put_catalog_pdf(pid)
    restored = await client.patch(f"/v1/admin/catalog/products/{pid}", json={"is_active": True}, headers=h)
    assert restored.json()["is_active"] is True
    assert (await client.get(f"/v1/catalog/products/{pid}")).json()["price_som"] == 33000


async def test_admin_catalog_rejects_unknown_category_and_non_admins(client):
    h = await _admin_headers()
    pid = (await client.get("/v1/admin/catalog/products", params={"limit": 1}, headers=h)).json()["items"][0]["id"]
    bad = await client.patch(f"/v1/admin/catalog/products/{pid}", json={"category_key": "yoq"}, headers=h)
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "bad_category"

    user = await register(client, phone="+998935554400")
    assert (await client.get("/v1/admin/catalog/products", headers=auth(user))).status_code == 403


async def test_receipt_link_opens_inline_for_admin(client):
    token = await register(client, phone="+998935554411")
    pid = (await client.post("/v1/payments", json={"kind": "plan_credit", "provider": "manual"}, headers=auth(token))).json()["payment"]["id"]
    await client.post(f"/v1/payments/{pid}/receipt", files={"file": ("chek.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")},
                      headers=auth(token))
    url = (await client.get(f"/v1/admin/payments/{pid}/receipt", headers=await _admin_headers())).json()["url"]
    r = await client.get(url.replace("http://test", ""))
    assert r.status_code == 200 and r.headers["content-disposition"].startswith("inline")
    assert r.headers["content-type"] == "image/png"
