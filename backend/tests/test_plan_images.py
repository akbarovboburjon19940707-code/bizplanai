"""Muqova rasmi (yuklash va avtomatik) va JShShIR."""
import struct
import zlib

import httpx
import pytest
from docx import Document

from tests.conftest import PLAN_INPUT, auth, register


def png(w: int = 40, h: int = 24) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + b"\x80\x80\x80" * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


async def upload(client, token, data: bytes, name="rasm.png"):
    return await client.post("/v1/plans/images", files={"file": (name, data, "image/png")}, headers=auth(token))


async def plan_docx(client, token, **extra):
    plan = (await client.post("/v1/plans", json={"input": {**PLAN_INPUT, **extra}}, headers=auth(token))).json()
    assert plan["status"] == "done", plan
    url = (await client.get(f"/v1/plans/{plan['id']}/download", headers=auth(token))).json()["url"]
    from app.core.security import decode_token
    from app.storage import get_storage
    return Document(get_storage().path_for(decode_token(url.rsplit("/", 1)[-1], "file")["key"]))


async def test_upload_validation(client):
    assert (await client.post("/v1/plans/images", files={"file": ("a.png", png(), "image/png")})).status_code == 401
    token = await register(client)
    r = await upload(client, token, png())
    assert r.status_code == 201 and r.json()["image_id"].endswith(".png") and len(r.json()["image_id"]) == 36
    assert (await upload(client, token, b"%PDF-1.4 ...", "a.pdf")).json()["error"]["code"] == "bad_file"
    assert (await upload(client, token, b"RIFF0000WEBPVP8 ")).json()["error"]["code"] == "bad_file"
    big = png() + b"\x00" * (5 * 1024 * 1024)
    assert (await upload(client, token, big)).status_code == 413


async def test_uploaded_image_on_cover_only_for_owner(client):
    owner = await register(client)
    image_id = (await upload(client, owner, png())).json()["image_id"]
    doc = await plan_docx(client, owner, rasm_id=image_id, rasm_avto=False)
    assert len(doc.inline_shapes) == 1

    other = await register(client, phone="+998907778899")
    doc = await plan_docx(client, other, rasm_id=image_id, rasm_avto=False)  # boshqa foydalanuvchi rasmi ishlamaydi
    assert len(doc.inline_shapes) == 0


async def test_auto_image_used_when_no_upload(client, monkeypatch):
    import app.modules.plans.service as svc
    calls = []

    async def fake_fetch(ctx):
        calls.append(ctx["faoliyat_turi"])
        return png()
    monkeypatch.setattr(svc, "fetch_cover_image", fake_fetch)
    token = await register(client)
    assert len((await plan_docx(client, token)).inline_shapes) == 1
    assert calls == ["ishlab_chiqarish"]
    assert len((await plan_docx(client, token, rasm_avto=False)).inline_shapes) == 0
    assert calls == ["ishlab_chiqarish"]


async def test_fetch_cover_image_pexels(monkeypatch):
    import app.ai.images as images
    from app.core.config import get_settings
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "api.pexels.com":
            seen["query"], seen["auth"] = request.url.params["query"], request.headers["authorization"]
            return httpx.Response(200, json={"photos": [
                {"src": {"large": "https://evil.example.com/x.jpg"}},       # ruxsat etilmagan host
                {"src": {"large": "https://images.pexels.com/photos/1/a.png"}},
            ]})
        assert request.url.host == "images.pexels.com"
        return httpx.Response(200, content=png())

    real = httpx.AsyncClient
    monkeypatch.setattr(images.httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), **kw))
    assert await images.fetch_cover_image({"faoliyat_turi": "savdo"}) is None  # kalit yo'q: o'chiq

    monkeypatch.setattr(get_settings(), "pexels_api_key", "test-key")
    monkeypatch.setattr(get_settings(), "ai_enabled", False)
    data = await images.fetch_cover_image({"faoliyat_turi": "savdo"})
    assert data and data.startswith(b"\x89PNG")
    assert seen == {"query": "grocery store shop shelves", "auth": "test-key"}


async def test_jshshir_manual_field(client):
    token = await register(client)
    assert (await client.post("/v1/plans/preview", json={**PLAN_INPUT, "jshshir": "123"})).status_code == 422
    doc = await plan_docx(client, token, jshshir="30101900000012", rasm_avto=False)
    rows = {r.cells[1].text.strip(): r.cells[2].text.strip() for t in doc.tables for r in t.rows
            if len(r.cells) >= 3 and r.cells[1].text.strip() == "JSHSHIR:"}
    assert rows == {"JSHSHIR:": "30101900000012"}


@pytest.mark.parametrize("bad", ["../x.png", "a" * 32 + ".gif", "A" * 32 + ".png"])
async def test_rasm_id_format(client, bad):
    r = await client.post("/v1/plans/preview", json={**PLAN_INPUT, "rasm_id": bad})
    assert r.status_code == 422


def test_picture_id_unique_across_parts(tmp_path):
    """Header'dagi shakllar bilan bir xil docPr id bo'lsa Word faylni ochmaydi."""
    import re
    import zipfile

    from app.engine.financial_engine import calculate_financial_model
    from app.engine.word_generator import generate_word_report
    path = tmp_path / "r.docx"
    generate_word_report(calculate_financial_model(PLAN_INPUT), str(path), None, png())
    with zipfile.ZipFile(path) as z:
        ids = [i for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)
               for i in re.findall(r'<wp:docPr id="(\d+)"', z.read(n).decode())]
    assert len(ids) == len(set(ids)) >= 2
