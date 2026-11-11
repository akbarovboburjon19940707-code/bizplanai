import base64
import hashlib
import time

from sqlalchemy import select

from tests.conftest import PLAN_INPUT, auth, put_catalog_pdf, register, remove_catalog_pdf

PAYME_AUTH = {"Authorization": "Basic " + base64.b64encode(b"Paycom:payme-key").decode()}


def click_form(payment_id, amount_som, action, click_trans_id="9001", prepare_id="", error="0", secret="click-secret"):
    f = {"click_trans_id": click_trans_id, "service_id": "11111", "click_paydoc_id": "1",
         "merchant_trans_id": payment_id, "amount": f"{amount_som}.00", "action": str(action),
         "error": error, "error_note": "", "sign_time": "2026-11-09 12:00:00"}
    if action == 1:
        f["merchant_prepare_id"] = str(prepare_id)
    raw = (f"{f['click_trans_id']}{f['service_id']}{secret}{payment_id}{f.get('merchant_prepare_id', '')}"
           f"{f['amount']}{f['action']}{f['sign_time']}")
    f["sign_string"] = hashlib.md5(raw.encode()).hexdigest()
    return f


async def test_methods_and_server_side_price(client):
    token = await register(client)
    assert (await client.get("/v1/payments/methods")).json() == {"click": True, "payme": True, "manual": True}
    r = await client.post("/v1/payments", json={"kind": "subscription", "target_id": "pro", "provider": "click"},
                          headers=auth(token))
    assert r.status_code == 201
    assert r.json()["payment"]["amount_som"] == 50000
    assert r.json()["checkout"]["url"].startswith("https://my.click.uz/services/pay?")
    bad = await client.post("/v1/payments", json={"kind": "subscription", "target_id": "basic", "provider": "click"},
                            headers=auth(token))
    assert bad.status_code == 404


async def test_click_subscription_flow(client):
    token = await register(client)
    pid = (await client.post("/v1/payments", json={"kind": "subscription", "target_id": "pro", "provider": "click"},
                             headers=auth(token))).json()["payment"]["id"]

    wrong_sign = click_form(pid, 50000, 0, secret="xato")
    assert (await client.post("/v1/payments/click/prepare", data=wrong_sign)).json()["error"] == -1
    wrong_amount = click_form(pid, 100, 0)
    assert (await client.post("/v1/payments/click/prepare", data=wrong_amount)).json()["error"] == -2

    prep = (await client.post("/v1/payments/click/prepare", data=click_form(pid, 50000, 0))).json()
    assert prep["error"] == 0
    bad_prep = click_form(pid, 50000, 1, prepare_id=999)
    assert (await client.post("/v1/payments/click/complete", data=bad_prep)).json()["error"] == -6

    done = (await client.post("/v1/payments/click/complete",
                              data=click_form(pid, 50000, 1, prepare_id=prep["merchant_prepare_id"]))).json()
    assert done["error"] == 0
    again = (await client.post("/v1/payments/click/complete",
                               data=click_form(pid, 50000, 1, prepare_id=prep["merchant_prepare_id"]))).json()
    assert again["error"] == -4  # takroriy callback huquqni ikki marta bermaydi

    me = (await client.get("/v1/me", headers=auth(token))).json()["subscription"]
    assert me["tariff_code"] == "pro" and me["status"] == "active" and me["daily_limit"] == 15

    plan = (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))).json()
    assert plan["quota_source"] == "subscription" and plan["ai_requested"] is True

    from app.db.session import sessionmaker
    from app.models import Subscription
    async with sessionmaker()() as s:
        assert len((await s.scalars(select(Subscription))).all()) == 1


async def test_payme_catalog_flow(client):
    token = await register(client)
    products = (await client.get("/v1/catalog/products", params={"limit": 1})).json()
    assert products["total"] == 269
    prod = products["items"][0]
    assert prod["price_som"] == 25000
    await put_catalog_pdf(prod["id"])

    assert (await client.get(f"/v1/catalog/products/{prod['id']}/download", headers=auth(token))).status_code == 403

    r = await client.post("/v1/payments", json={"kind": "catalog", "target_id": prod["id"], "provider": "payme"},
                          headers=auth(token))
    pid, amount = r.json()["payment"]["id"], 25000 * 100

    def rpc(method, params, rid=1, headers=PAYME_AUTH):
        return client.post("/v1/payments/payme", json={"id": rid, "method": method, "params": params}, headers=headers)

    assert (await rpc("CheckPerformTransaction", {"amount": amount, "account": {"order_id": pid}},
                      headers={})).json()["error"]["code"] == -32504
    assert (await rpc("CheckPerformTransaction", {"amount": 1, "account": {"order_id": pid}})).json()["error"]["code"] == -31001
    assert (await rpc("CheckPerformTransaction", {"amount": amount, "account": {"order_id": pid}})).json()["result"]["allow"]

    now = int(time.time() * 1000)
    created = (await rpc("CreateTransaction", {"id": "pm1", "time": now, "amount": amount, "account": {"order_id": pid}})).json()
    assert created["result"]["state"] == 1
    other = (await rpc("CreateTransaction", {"id": "pm2", "time": now, "amount": amount, "account": {"order_id": pid}})).json()
    assert other["error"]["code"] == -31050

    performed = (await rpc("PerformTransaction", {"id": "pm1"})).json()
    assert performed["result"]["state"] == 2
    assert (await rpc("PerformTransaction", {"id": "pm1"})).json()["result"]["state"] == 2  # idempotent

    # Sotilgandan keyin fayl yo'qolsa -> aniq xato (pul olingan, admin faylni tiklaydi)
    await remove_catalog_pdf(prod["id"])
    r = await client.get(f"/v1/catalog/products/{prod['id']}/download", headers=auth(token))
    assert r.status_code == 404 and r.json()["error"]["code"] == "file_missing"
    from app.storage import get_storage
    from app.db.session import sessionmaker
    from app.models import CatalogProduct
    async with sessionmaker()() as s:
        key = (await s.get(CatalogProduct, prod["id"])).file_key
    await get_storage().put_bytes(key, b"%PDF-1.4 test", "application/pdf")
    r = await client.get(f"/v1/catalog/products/{prod['id']}/download", headers=auth(token))
    assert r.status_code == 200
    assert (await client.get(r.json()["url"].replace("http://test", ""))).content.startswith(b"%PDF")

    # sotib olingan narsani qayta sotib bo'lmaydi
    again = await client.post("/v1/payments", json={"kind": "catalog", "target_id": prod["id"], "provider": "payme"},
                              headers=auth(token))
    assert again.status_code == 409

    cancelled = (await rpc("CancelTransaction", {"id": "pm1", "reason": 5})).json()
    assert cancelled["result"]["state"] == -2
    assert (await client.get(f"/v1/catalog/products/{prod['id']}/download", headers=auth(token))).status_code == 403

    stmt = (await rpc("GetStatement", {"from": now - 1000, "to": now + 1000})).json()
    assert len(stmt["result"]["transactions"]) == 1


async def test_manual_receipt_and_admin_approval(client):
    from app.cli import create_admin
    from app.db.session import sessionmaker
    from app.models import User

    token = await register(client)
    r = await client.post("/v1/payments", json={"kind": "plan_credit", "provider": "manual"}, headers=auth(token))
    assert r.json()["checkout"]["type"] == "manual"
    pid = r.json()["payment"]["id"]

    bad = await client.post(f"/v1/payments/{pid}/receipt", files={"file": ("a.png", b"<script>", "image/png")},
                            headers=auth(token))
    assert bad.status_code == 400
    ok = await client.post(f"/v1/payments/{pid}/receipt",
                           files={"file": ("chek.png", b"\x89PNG\r\n\x1a\n" + b"0" * 100, "image/png")}, headers=auth(token))
    assert ok.status_code == 200 and ok.json()["status"] == "reviewing"

    await create_admin("+998909998877", "juda-kuchli-parol-123")
    async with sessionmaker()() as s:
        admin = (await s.scalars(select(User).where(User.role == "admin"))).one()
    from app.core.security import create_access_token
    admin_h = auth(create_access_token(admin.id, "admin"))

    queue = (await client.get("/v1/admin/payments", params={"status": "reviewing"}, headers=admin_h)).json()
    assert [p["id"] for p in queue] == [pid] and queue[0]["has_receipt"]
    assert (await client.get(f"/v1/admin/payments/{pid}/receipt", headers=admin_h)).status_code == 200
    assert (await client.post(f"/v1/admin/payments/{pid}/approve", json={"note": "ok"}, headers=admin_h)).json()["status"] == "paid"
    again = await client.post(f"/v1/admin/payments/{pid}/approve", json={}, headers=admin_h)
    assert again.status_code == 409

    me = (await client.get("/v1/me", headers=auth(token))).json()
    assert me["user"]["plan_credits"] == 1


async def test_credit_used_after_free_limit(client):
    from app.db.session import sessionmaker
    from app.models import User
    from sqlalchemy import update

    token = await register(client)
    async with sessionmaker()() as s:
        await s.execute(update(User).values(plan_credits=1))
        await s.commit()
    # kredit bepul limitdan oldin sarflanadi va AI beradi
    plan = (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))).json()
    assert plan["quota_source"] == "credit" and plan["ai_requested"] is True
    plan2 = (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))).json()
    assert plan2["quota_source"] == "free"


async def test_click_failed_second_tx_does_not_revoke_paid(client):
    token = await register(client)
    pid = (await client.post("/v1/payments", json={"kind": "subscription", "target_id": "pro", "provider": "click"},
                             headers=auth(token))).json()["payment"]["id"]
    p1 = (await client.post("/v1/payments/click/prepare", data=click_form(pid, 50000, 0, click_trans_id="1"))).json()
    p2 = (await client.post("/v1/payments/click/prepare", data=click_form(pid, 50000, 0, click_trans_id="2"))).json()
    ok = (await client.post("/v1/payments/click/complete", data=click_form(
        pid, 50000, 1, click_trans_id="1", prepare_id=p1["merchant_prepare_id"]))).json()
    assert ok["error"] == 0
    failed = (await client.post("/v1/payments/click/complete", data=click_form(
        pid, 50000, 1, click_trans_id="2", prepare_id=p2["merchant_prepare_id"], error="-5017"))).json()
    assert failed["error"] == -9
    sub = (await client.get("/v1/me", headers=auth(token))).json()["subscription"]
    assert sub["tariff_code"] == "pro" and sub["status"] == "active"


async def test_catalog_plan_without_file_cannot_be_bought(client):
    """Fayli yo'q reja: to'lov yaratilmaydi (pul olinmaydi), fayl qo'yilgach sotiladi."""
    from app.db.session import sessionmaker
    from app.models import Payment

    token = await register(client)
    pid = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]["id"]
    await remove_catalog_pdf(pid)
    r = await client.post("/v1/payments", json={"kind": "catalog", "target_id": pid, "provider": "manual"}, headers=auth(token))
    assert r.status_code == 409 and r.json()["error"]["code"] == "file_missing"
    async with sessionmaker()() as s:
        assert (await s.scalars(select(Payment))).first() is None

    await put_catalog_pdf(pid)
    r = await client.post("/v1/payments", json={"kind": "catalog", "target_id": pid, "provider": "manual"}, headers=auth(token))
    assert r.status_code == 201


async def test_payme_sandbox_scenarios(client):
    """Payme sandbox (test kassa) tekshiradigan holatlar: xato kodlari, bekor qilish, muddat, javob shakli."""
    from sqlalchemy import update

    from app.db.session import sessionmaker
    from app.models import Payment, PaymeTransaction

    token = await register(client)

    async def new_payment():
        r = await client.post("/v1/payments", json={"kind": "plan_credit", "provider": "payme"}, headers=auth(token))
        p = r.json()["payment"]
        assert "l=uz" in base64.b64decode(r.json()["checkout"]["url"].rsplit("/", 1)[1]).decode()
        return p["id"], p["amount_som"] * 100

    def rpc(method, params, headers=PAYME_AUTH):
        return client.post("/v1/payments/payme", json={"id": 7, "method": method, "params": params}, headers=headers)

    pid, amount = await new_payment()
    wrong = {"Authorization": "Basic " + base64.b64encode(b"Paycom:xato").decode()}
    err = (await rpc("CheckPerformTransaction", {"amount": amount, "account": {"order_id": pid}}, wrong)).json()["error"]
    assert err["code"] == -32504 and set(err["message"]) == {"uz", "ru", "en"} and err["message"]["ru"] != err["message"]["uz"]
    err = (await rpc("CheckPerformTransaction", {"amount": amount, "account": {"order_id": "yoq"}})).json()["error"]
    assert err["code"] == -31050 and err["data"] == "order_id"
    assert (await rpc("PerformTransaction", {"id": "yoq"})).json()["error"]["code"] == -31003
    assert (await rpc("CancelTransaction", {"id": "yoq", "reason": 1})).json()["error"]["code"] == -31003
    assert (await rpc("CheckTransaction", {"id": "yoq"})).json()["error"]["code"] == -31003
    assert (await rpc("ChangePassword", {})).json()["error"]["code"] == -32601
    bad = await client.post("/v1/payments/payme", content=b"{not json", headers={**PAYME_AUTH, "content-type": "application/json"})
    assert bad.json()["error"]["code"] == -32700

    # Yaratilgan (to'lanmagan) tranzaksiyani bekor qilish: state -1, buyurtma yopiladi
    now = int(time.time() * 1000)
    created = (await rpc("CreateTransaction", {"id": "sb1", "time": now, "amount": amount, "account": {"order_id": pid}})).json()
    assert created["result"]["state"] == 1
    again = (await rpc("CreateTransaction", {"id": "sb1", "time": now, "amount": amount, "account": {"order_id": pid}})).json()
    assert again["result"]["transaction"] == created["result"]["transaction"]  # takroriy so'rov: o'sha javob
    check = (await rpc("CheckTransaction", {"id": "sb1"})).json()["result"]
    assert check["perform_time"] == 0 and check["cancel_time"] == 0 and check["reason"] is None and check["state"] == 1
    c1 = (await rpc("CancelTransaction", {"id": "sb1", "reason": 3})).json()["result"]
    assert c1["state"] == -1 and c1["cancel_time"] > 0
    c2 = (await rpc("CancelTransaction", {"id": "sb1", "reason": 3})).json()["result"]
    assert c2 == c1  # idempotent
    assert (await rpc("PerformTransaction", {"id": "sb1"})).json()["error"]["code"] == -31008
    assert (await rpc("CheckTransaction", {"id": "sb1"})).json()["result"]["reason"] == 3
    closed = (await rpc("CheckPerformTransaction", {"amount": amount, "account": {"order_id": pid}})).json()["error"]
    assert -31099 <= closed["code"] <= -31050
    me = (await client.get("/v1/me", headers=auth(token))).json()
    assert me["user"]["plan_credits"] == 0

    # 12 soatdan keyin bajarish: -31008, reason 4, huquq berilmaydi
    pid2, amount2 = await new_payment()
    (await rpc("CreateTransaction", {"id": "sb2", "time": now, "amount": amount2, "account": {"order_id": pid2}})).json()
    async with sessionmaker()() as s:
        await s.execute(update(PaymeTransaction).where(PaymeTransaction.payme_id == "sb2")
                        .values(create_time=now - 43_200_001))
        await s.commit()
    assert (await rpc("PerformTransaction", {"id": "sb2"})).json()["error"]["code"] == -31008
    st = (await rpc("CheckTransaction", {"id": "sb2"})).json()["result"]
    assert st["state"] == -1 and st["reason"] == 4
    async with sessionmaker()() as s:
        assert (await s.get(Payment, pid2)).status != "paid"
    me = (await client.get("/v1/me", headers=auth(token))).json()
    assert me["user"]["plan_credits"] == 0
