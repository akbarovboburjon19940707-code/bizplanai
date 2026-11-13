"""Admin: katalogga reja qo'shish (PDF, rasm), o'chirish, saytni yangilash; foydalanuvchiga tarif va kredit berish."""
from datetime import datetime, timedelta

from tests.conftest import auth, register
from tests.test_admin import _admin_headers
from tests.test_payments import click_form

PDF = b"%PDF-1.4\n" + b"0" * 2048
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 128


async def _new_product(client, h, **extra):
    body = {"title": "Ўрдак боқиш fermasi", "category_key": "qishloq", "price_som": 30000, "description": "Tavsif", **extra}
    r = await client.post("/v1/admin/catalog/products", json=body, headers=h)
    assert r.status_code == 201, r.text
    return r.json()


async def test_add_product_upload_files_activate_and_delete(client):
    from app.storage import get_storage

    h = await _admin_headers()
    cats = (await client.get("/v1/catalog/categories")).json()
    p = await _new_product(client, h, category_key=cats[0]["key"])
    assert p["id"].startswith("p") and p["slug"] == "ordak-boqish-fermasi" and p["is_active"] is False
    assert p["file_key"] == f"catalog/pdfs/{p['id']}.pdf"
    again = await _new_product(client, h, category_key=cats[0]["key"])  # bir xil nom: slug takrorlanmaydi
    assert again["slug"] == "ordak-boqish-fermasi-2"
    assert (await client.get(f"/v1/catalog/products/{p['id']}")).status_code == 404  # yashirin

    url = f"/v1/admin/catalog/products/{p['id']}"
    assert (await client.patch(url, json={"is_active": True}, headers=h)).status_code == 409  # faylsiz
    bad = await client.post(f"{url}/file", files={"file": ("x.pdf", b"not a pdf", "application/pdf")}, headers=h)
    assert bad.status_code == 400
    ok = await client.post(f"{url}/file", files={"file": ("reja.pdf", PDF, "application/pdf")}, headers=h)
    assert ok.status_code == 200 and ok.json()["file_size"] == "2 KB"
    img = await client.post(f"{url}/image", files={"file": ("m.png", PNG, "image/png")}, headers=h)
    assert img.status_code == 200 and f"/v1/catalog/products/{p['id']}/thumb?v=" in img.json()["preview_image"]
    assert (await client.post(f"{url}/image", files={"file": ("m.gif", b"GIF89a", "image/gif")}, headers=h)).status_code == 400
    active = await client.patch(url, json={"is_active": True}, headers=h)
    assert active.json()["is_active"] is True
    assert (await client.get(f"/v1/catalog/products/{p['id']}")).json()["price_som"] == 30000

    # sotilmagan: butunlay o'chadi, fayllari ham
    assert (await client.delete(url, headers=h)).status_code == 204
    assert (await client.get(f"/v1/catalog/products/{p['id']}")).status_code == 404
    assert not await get_storage().exists(p["file_key"])
    assert (await client.delete(url, headers=h)).status_code == 404


async def test_sold_product_cannot_be_deleted_and_non_admin_blocked(client):
    from tests.conftest import put_catalog_pdf

    h = await _admin_headers()
    prod = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]
    await put_catalog_pdf(prod["id"])
    token = await register(client)
    await client.post("/v1/payments", json={"kind": "catalog", "target_id": prod["id"], "provider": "manual"}, headers=auth(token))
    r = await client.delete(f"/v1/admin/catalog/products/{prod['id']}", headers=h)
    assert r.status_code == 409 and r.json()["error"]["code"] == "product_sold"
    assert (await client.delete(f"/v1/admin/catalog/products/{prod['id']}", headers=auth(token))).status_code == 403
    assert (await client.post("/v1/admin/catalog/products", json={"title": "x" * 5, "category_key": "a", "price_som": 1},
                              headers=auth(token))).status_code == 403


async def test_site_rebuild_hook(client, monkeypatch):
    from app.core.config import get_settings

    h = await _admin_headers()
    assert (await client.post("/v1/admin/site/rebuild", headers=h)).status_code == 503  # sozlanmagan
    calls = []

    class FakeClient:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def post(self, url):
            import httpx
            calls.append(url)
            return httpx.Response(200, request=httpx.Request("POST", url))

    monkeypatch.setattr(get_settings(), "frontend_deploy_hook_url", "https://api.render.com/deploy/srv-x?key=y")
    monkeypatch.setattr("app.modules.admin.catalog_files.httpx.AsyncClient", FakeClient)
    assert (await client.post("/v1/admin/site/rebuild", headers=h)).json() == {"triggered": True}
    assert calls == ["https://api.render.com/deploy/srv-x?key=y"]
    assert (await client.post("/v1/admin/site/rebuild", headers=h)).status_code == 429  # 2 daqiqada bir marta


async def test_admin_grants_subscription_credits_and_revokes(client):
    h = await _admin_headers()
    token = await register(client, phone="+998935550101")
    uid = (await client.get("/v1/me", headers=auth(token))).json()["user"]["id"]

    sub = await client.post(f"/v1/admin/users/{uid}/grant", json={"kind": "subscription", "tariff_code": "pro", "days": 7,
                                                                   "note": "Hamkor"}, headers=h)
    assert sub.status_code == 200, sub.text
    body = sub.json()
    assert body["subscriptions"][0]["source"] == "admin" and body["subscriptions"][0]["status"] == "active"
    ends = datetime.fromisoformat(body["subscriptions"][0]["ends_at"].rstrip("Z"))
    assert timedelta(days=6, hours=23) < ends - datetime.utcnow() <= timedelta(days=7)
    me = (await client.get("/v1/me", headers=auth(token))).json()
    assert me["subscription"]["tariff_code"] == "pro" and me["subscription"]["monthly_limit"] == 10

    cr = (await client.post(f"/v1/admin/users/{uid}/grant", json={"kind": "credits", "count": 3}, headers=h)).json()
    assert cr["user"]["plan_credits"] == 3 and len(cr["grants"]) == 4  # 1 obuna + 3 kredit
    assert all(g["status"] == "paid" for g in cr["grants"])
    stats = (await client.get("/v1/admin/stats", headers=h)).json()
    assert stats["revenue_som"] == 0  # admin berganlari tushum emas

    assert (await client.post(f"/v1/admin/users/{uid}/grant", json={"kind": "subscription", "tariff_code": "basic"},
                              headers=h)).status_code == 400
    assert (await client.post(f"/v1/admin/users/{uid}/grant", json={"kind": "credits", "count": 21},
                              headers=h)).status_code == 422
    assert (await client.post(f"/v1/admin/users/{uid}/grant", json={"kind": "credits", "count": 1},
                              headers=auth(token))).status_code == 403

    sid = cr["subscriptions"][0]["id"]
    rev = (await client.post(f"/v1/admin/subscriptions/{sid}/revoke", json={"note": "xato berildi"}, headers=h)).json()
    assert rev["subscriptions"][0]["status"] == "revoked"
    assert next(g for g in rev["grants"] if g["kind"] == "subscription")["status"] == "cancelled"
    assert (await client.get("/v1/me", headers=auth(token))).json()["subscription"]["tariff_code"] == "basic"
    assert (await client.post(f"/v1/admin/subscriptions/{sid}/revoke", json={}, headers=h)).status_code == 409


async def test_revoking_a_paid_subscription_keeps_the_payment_record(client):
    h = await _admin_headers()
    token = await register(client, phone="+998935550202")
    pid = (await client.post("/v1/payments", json={"kind": "subscription", "target_id": "pro", "provider": "click"},
                             headers=auth(token))).json()["payment"]["id"]
    prep = (await client.post("/v1/payments/click/prepare", data=click_form(pid, 200000, 0))).json()
    await client.post("/v1/payments/click/complete", data=click_form(pid, 200000, 1, prepare_id=prep["merchant_prepare_id"]))
    uid = (await client.get("/v1/me", headers=auth(token))).json()["user"]["id"]
    billing = (await client.get(f"/v1/admin/users/{uid}/billing", headers=h)).json()
    assert billing["subscriptions"][0]["source"] == "payment" and [t["code"] for t in billing["tariffs"]] == ["pro", "enterprise"]
    await client.post(f"/v1/admin/subscriptions/{billing['subscriptions'][0]['id']}/revoke", json={}, headers=h)
    paid = (await client.get(f"/v1/payments/{pid}", headers=auth(token))).json()["payment"]
    assert paid["status"] == "paid"  # pul qaytarish alohida: to'lov yozuvi o'zgarmaydi
