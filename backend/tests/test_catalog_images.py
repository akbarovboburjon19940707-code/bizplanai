"""Yopiq bucket: katalog rasmlari va PDF faqat backend orqali, imzolangan havola bilan."""
import io
import re

import pytest
from PIL import Image

from app.storage import get_storage

from app.modules.catalog.router import image_key, thumb_key


async def test_preview_image_points_to_backend_not_r2_dev(client):
    page = (await client.get("/v1/catalog/products", params={"limit": 5})).json()
    for item in page["items"]:
        assert "r2.dev" not in item["preview_image"]
        assert re.fullmatch(rf"http://test/v1/catalog/products/{item['id']}/thumb\?v=[0-9a-f]{{10}}", item["preview_image"])


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


def _png(w: int, h: int) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (w, h), (200, 30, 30)).save(out, "PNG")
    return out.getvalue()


async def _product(pid: str):
    from app.db.session import sessionmaker
    from app.models import CatalogProduct

    async with sessionmaker()() as s:
        return await s.get(CatalogProduct, pid)


async def test_thumb_is_small_webp_with_immutable_cache(client):
    item = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]
    product = await _product(item["id"])
    storage = get_storage()
    await storage.put_bytes(image_key(product.preview_image), _png(1191, 1684), "image/png")

    url = item["preview_image"].removeprefix("http://test")
    r = await client.get(url)
    assert r.status_code == 200 and r.headers["content-type"] == "image/webp"
    assert r.headers["cache-control"] == "public, max-age=31536000, immutable"
    with Image.open(io.BytesIO(r.content)) as im:
        assert im.format == "WEBP" and im.size == (600, round(1684 * 600 / 1191))
    assert await storage.exists(thumb_key(product))  # keyingi so'rov tayyor nusxadan
    assert (await client.get(url)).content == r.content


async def test_thumb_broken_or_missing_image(client):
    item = (await client.get("/v1/catalog/products", params={"limit": 1})).json()["items"][0]
    url = item["preview_image"].removeprefix("http://test")
    product = await _product(item["id"])
    storage = get_storage()
    if await storage.exists(image_key(product.preview_image)):
        await storage.delete(image_key(product.preview_image))
    assert (await client.get(url)).status_code == 404  # asl rasm yo'q
    await storage.put_bytes(image_key(product.preview_image), b"not an image", "image/png")
    r = await client.get(url, follow_redirects=False)
    assert r.status_code == 302  # buzuq rasm: asl rasmga yo'naltiriladi
    assert (await client.get("/v1/catalog/products/yoq-mahsulot/thumb")).status_code == 404
