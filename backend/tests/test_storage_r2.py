"""R2 exists(): faqat "yo'q" javobi False; ruxsat/sozlama xatosi yashirilmaydi."""
import pytest
from botocore.exceptions import ClientError

from app.storage import R2Storage


class FakeS3:
    def __init__(self, code: str | None):
        self.code = code

    def head_object(self, Bucket, Key):  # noqa: N803 - boto3 imzosi
        if self.code:
            raise ClientError({"Error": {"Code": self.code, "Message": "x"}}, "HeadObject")
        return {}


def storage(code: str | None) -> R2Storage:
    s = R2Storage.__new__(R2Storage)
    s.client, s.bucket = FakeS3(code), "bucket"
    return s


async def test_existing_object():
    assert await storage(None).exists("catalog/pdfs/a.pdf") is True


@pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
async def test_missing_object_is_false(code):
    assert await storage(code).exists("catalog/pdfs/a.pdf") is False


@pytest.mark.parametrize("code", ["403", "AccessDenied", "InvalidAccessKeyId", "500"])
async def test_access_or_server_errors_are_raised(code):
    with pytest.raises(ClientError):
        await storage(code).exists("catalog/pdfs/a.pdf")
