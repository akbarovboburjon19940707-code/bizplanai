"""Yopiq bucket: katalog rasmlari va PDF faqat backend orqali, imzolangan havola bilan."""
import pytest

from app.modules.catalog.router import image_key


async def test_preview_image_points_to_backend_not_r2_dev(client):
    page = (await client.get("/v1/catalog/products", params={"limit": 5})).json()
    for item in page["items"]:
        assert "r2.dev" not in item["preview_image"]
        assert item["preview_image"] == f"http://test/v1/catalog/products/{item['id']}/image"


async def test_image_redirects_to_signed_inline_url(client):
    pid = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]["id"]
    r = await client.get(f"/v1/catalog/products/{pid}/image", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers["location"].startswith("http://test/v1/files/")  # dev: lokal imzolangan havola
    assert r.headers["cache-control"] == "public, max-age=1800"
    assert (await client.get("/v1/catalog/products/yoq-mahsulot/image")).status_code == 404


@pytest.mark.parametrize("value,expected", [
    ("https://pub-abc.r2.dev/catalog/images/a_p1.png", "catalog/images/a_p1.png"),
    ("catalog/images/b.jpg", "catalog/images/b.jpg"),
    ("https://pub-abc.r2.dev/catalog/pdfs/a.pdf", None),          # pullik PDF imzolanmaydi
    ("https://pub-abc.r2.dev/generated/x/reja.docx", None),       # mijoz hujjati imzolanmaydi
    ("catalog/images/../pdfs/a.png", None),
    ("", None),
])
def test_image_key_only_allows_catalog_images(value, expected):
    assert image_key(value) == expected


async def test_r2_signed_url_inline_for_images():
    from app.storage import R2Storage

    captured = {}

    class FakeClient:
        def generate_presigned_url(self, op, Params, ExpiresIn):
            captured.update(op=op, params=Params, ttl=ExpiresIn)
            return "https://signed.example/x"

    storage = object.__new__(R2Storage)
    storage.bucket, storage.client = "private-bucket", FakeClient()
    await storage.signed_url("catalog/images/a.png", "a.png", 3600, inline=True)
    assert captured["params"]["ResponseContentDisposition"].startswith("inline;")
    await storage.signed_url("catalog/pdfs/a.pdf", "a.pdf", 600)
    assert captured["params"]["ResponseContentDisposition"].startswith("attachment;") and captured["ttl"] == 600
