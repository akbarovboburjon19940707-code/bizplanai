"""Fayl saqlash: production'da Cloudflare R2 (S3 API, yopiq bucket + imzolangan havola), dev'da lokal papka."""
import asyncio
import os
import shutil
from urllib.parse import quote

from app.core.config import get_settings
from app.core.security import sign_payload


class Storage:
    async def put_file(self, key: str, path: str, content_type: str) -> None: ...
    async def put_bytes(self, key: str, data: bytes, content_type: str) -> None: ...
    async def exists(self, key: str) -> bool: ...
    async def get_bytes(self, key: str, max_bytes: int) -> bytes | None: ...
    async def signed_url(self, key: str, filename: str, ttl: int | None = None, inline: bool = False) -> str: ...


class LocalStorage(Storage):
    def __init__(self, root: str):
        self.root = os.path.abspath(root)

    def path_for(self, key: str) -> str:
        path = os.path.abspath(os.path.join(self.root, key))
        if not path.startswith(self.root + os.sep):
            raise ValueError("Noto'g'ri kalit")
        return path

    async def put_file(self, key, path, content_type):
        dest = self.path_for(key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        await asyncio.to_thread(shutil.copyfile, path, dest)

    async def put_bytes(self, key, data, content_type):
        dest = self.path_for(key)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        await asyncio.to_thread(_write, dest, data)

    async def exists(self, key):
        return os.path.isfile(self.path_for(key))

    async def get_bytes(self, key, max_bytes):
        path = self.path_for(key)
        if not os.path.isfile(path) or os.path.getsize(path) > max_bytes:
            return None
        return await asyncio.to_thread(_read, path)

    async def signed_url(self, key, filename, ttl=None, inline=False):
        s = get_settings()
        payload = {"key": key, "fn": filename, **({"in": 1} if inline else {})}  # R2 dagi kabi inline/attachment
        token = sign_payload(payload, ttl or s.download_url_ttl_seconds, "file")
        return f"{s.public_api_url.rstrip('/')}/v1/files/{token}"


def _write(path: str, data: bytes) -> None:
    with open(path, "wb") as f:
        f.write(data)


def _read(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


class R2Storage(Storage):
    def __init__(self):
        import boto3
        from botocore.config import Config

        s = get_settings()
        self.bucket = s.r2_bucket
        self.client = boto3.client(
            "s3", endpoint_url=f"https://{s.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=s.r2_access_key_id, aws_secret_access_key=s.r2_secret_access_key,
            region_name="auto", config=Config(signature_version="s3v4", retries={"max_attempts": 3}),
        )

    async def put_file(self, key, path, content_type):
        await asyncio.to_thread(self.client.upload_file, path, self.bucket, key, ExtraArgs={"ContentType": content_type})

    async def put_bytes(self, key, data, content_type):
        await asyncio.to_thread(self.client.put_object, Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    async def exists(self, key):
        from botocore.exceptions import ClientError

        try:
            await asyncio.to_thread(self.client.head_object, Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            # Faqat "yo'q" javobi False: kalit/ruxsat xatosi (403 va h.k.) yashirilmaydi, aks holda
            # sozlama xatosi "hamma fayl yo'q" bo'lib ko'rinadi va katalog savdosi to'xtaydi
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    async def get_bytes(self, key, max_bytes):
        from botocore.exceptions import ClientError

        try:
            obj = await asyncio.to_thread(self.client.get_object, Bucket=self.bucket, Key=key)
        except ClientError:
            return None
        if obj.get("ContentLength", 0) > max_bytes:
            return None
        return await asyncio.to_thread(obj["Body"].read)

    async def signed_url(self, key, filename, ttl=None, inline=False):
        ttl = ttl or get_settings().download_url_ttl_seconds
        disposition = f"{'inline' if inline else 'attachment'}; filename*=UTF-8''{quote(filename)}"
        return await asyncio.to_thread(
            self.client.generate_presigned_url, "get_object",
            Params={"Bucket": self.bucket, "Key": key, "ResponseContentDisposition": disposition}, ExpiresIn=ttl,
        )


_storage: Storage | None = None


def get_storage() -> Storage:
    global _storage
    if _storage is None:
        s = get_settings()
        _storage = R2Storage() if s.storage_backend == "r2" else LocalStorage(s.local_storage_dir)
    return _storage


def set_storage(storage: Storage | None) -> None:
    global _storage
    _storage = storage
