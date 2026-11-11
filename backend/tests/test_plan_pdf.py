"""Reja PDF'i: Word -> PDF (LibreOffice), ixtiyoriy format."""
import os
import stat

import pytest

from app.core.config import get_settings
from app.engine import pdf as pdf_engine
from tests.conftest import PLAN_INPUT, auth, register


@pytest.fixture
def pdf_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "pdf_enabled", True)
    monkeypatch.setattr(pdf_engine, "_semaphore", None)


async def _create_plan(client) -> tuple[dict, dict]:
    h = auth(await register(client))
    r = await client.post("/v1/plans", json={"input": PLAN_INPUT, "use_ai": False}, headers=h)
    assert r.status_code == 202, r.text
    plan = (await client.get(f"/v1/plans/{r.json()['id']}", headers=h)).json()
    assert plan["status"] == "done"
    return plan, h


@pytest.mark.skipif(not pdf_engine.soffice_binary(), reason="LibreOffice (soffice) o'rnatilmagan")
async def test_plan_gets_a_real_pdf(client, pdf_on):
    plan, h = await _create_plan(client)
    assert plan["has_pdf"] is True
    url = (await client.get(f"/v1/plans/{plan['id']}/download", params={"format": "pdf"}, headers=h)).json()["url"]
    r = await client.get(url.replace("http://test", ""))
    assert r.status_code == 200 and r.content.startswith(b"%PDF") and len(r.content) > 5_000
    assert "biznes%20reja.pdf" in r.headers["content-disposition"]


async def test_plan_is_done_without_pdf_when_conversion_fails(client, pdf_on, monkeypatch):
    async def broken(docx_path, out_dir):
        return None

    monkeypatch.setattr("app.modules.plans.service.docx_to_pdf", broken)
    plan, h = await _create_plan(client)
    assert plan["has_pdf"] is False
    r = await client.get(f"/v1/plans/{plan['id']}/download", params={"format": "pdf"}, headers=h)
    assert r.status_code == 404 and r.json()["error"]["code"] == "pdf_unavailable"
    assert (await client.get(f"/v1/plans/{plan['id']}/download", params={"format": "docx"}, headers=h)).status_code == 200


async def test_disabled_pdf_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "pdf_enabled", False)
    assert await pdf_engine.docx_to_pdf(str(tmp_path / "a.docx"), str(tmp_path)) is None


async def test_hanging_soffice_is_killed_after_timeout(tmp_path, monkeypatch, pdf_on):
    fake = tmp_path / "soffice"
    fake.write_text("#!/bin/sh\nsleep 30\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(get_settings(), "pdf_timeout_seconds", 0.5)
    assert pdf_engine.soffice_binary() == str(fake)
    assert await pdf_engine.docx_to_pdf(str(tmp_path / "a.docx"), str(tmp_path)) is None


async def test_failed_soffice_returns_none(tmp_path, monkeypatch, pdf_on):
    fake = tmp_path / "soffice"
    fake.write_text("#!/bin/sh\necho 'source file could not be loaded' >&2\nexit 1\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{tmp_path}{os.pathsep}{os.environ['PATH']}")
    assert await pdf_engine.docx_to_pdf(str(tmp_path / "a.docx"), str(tmp_path)) is None
