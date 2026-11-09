"""Faqat lokal saqlash rejimi uchun: imzolangan havola orqali fayl berish (R2'da havola to'g'ridan R2 ga boradi)."""
import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.core.errors import AppError
from app.core.security import decode_token
from app.storage import LocalStorage, get_storage

router = APIRouter(prefix="/v1/files", tags=["files"], include_in_schema=False)


@router.get("/{token}")
async def download(token: str):
    payload = decode_token(token, "file")
    storage = get_storage()
    if not payload or not isinstance(storage, LocalStorage):
        raise AppError(403, "link_expired", "Havola eskirgan yoki yaroqsiz")
    path = storage.path_for(payload["key"])
    if not os.path.isfile(path):
        raise AppError(404, "file_missing", "Fayl topilmadi")
    return FileResponse(path, filename=payload["fn"])
