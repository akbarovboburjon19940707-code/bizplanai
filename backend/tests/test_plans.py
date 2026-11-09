
from tests.conftest import PLAN_INPUT, auth, register


async def test_preview_is_public(client):
    r = await client.post("/v1/plans/preview", json=PLAN_INPUT)
    assert r.status_code == 200, r.text
    assert "npv" in r.json()["indicators"]


async def test_preview_rejects_unknown_fields(client):
    r = await client.post("/v1/plans/preview", json={**PLAN_INPUT, "hacker": 1})
    assert r.status_code == 422


async def test_generate_download_and_quota(client):
    token = await register(client)
    r = await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))
    assert r.status_code == 202, r.text
    plan = r.json()
    assert plan["status"] == "done" and plan["quota_source"] == "free" and plan["ai_requested"] is False

    d = await client.get(f"/v1/plans/{plan['id']}/download", params={"format": "docx"}, headers=auth(token))
    assert d.status_code == 200
    f = await client.get(d.json()["url"].replace("http://test", ""))
    assert f.status_code == 200 and f.content[:2] == b"PK"  # docx = zip
    x = await client.get(f"/v1/plans/{plan['id']}/download", params={"format": "xlsx"}, headers=auth(token))
    assert (await client.get(x.json()["url"].replace("http://test", ""))).content[:2] == b"PK"

    # bepul tarif: kuniga 3 ta
    for _ in range(2):
        assert (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))).status_code == 202
    over = await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))
    assert over.status_code == 429 and over.json()["error"]["code"] == "quota_exceeded"

    me = (await client.get("/v1/me", headers=auth(token))).json()["subscription"]
    assert me["daily_used"] == 3


async def test_other_user_cannot_access_plan(client):
    t1 = await register(client, phone="+998900000001")
    t2 = await register(client, phone="+998900000002")
    plan = (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(t1))).json()
    assert (await client.get(f"/v1/plans/{plan['id']}", headers=auth(t2))).status_code == 404
    assert (await client.get(f"/v1/plans/{plan['id']}/download", headers=auth(t2))).status_code == 404


async def test_tampered_file_link_rejected(client):
    r = await client.get("/v1/files/not-a-valid-token")
    assert r.status_code == 403


async def test_failed_generation_refunds_quota(client, monkeypatch):
    import app.modules.plans.service as svc

    def boom(*a, **k):
        raise RuntimeError("disk to'ldi")
    monkeypatch.setattr(svc, "_render_files", boom)
    token = await register(client)
    plan = (await client.post("/v1/plans", json={"input": PLAN_INPUT}, headers=auth(token))).json()
    assert plan["status"] == "failed"
    me = (await client.get("/v1/me", headers=auth(token))).json()["subscription"]
    assert me["daily_used"] == 0
