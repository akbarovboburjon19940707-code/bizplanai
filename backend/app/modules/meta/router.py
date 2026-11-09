"""Forma uchun ma'lumotnomalar (eski categories.json): bir marta xotiraga yuklanadi, CDN keshlaydi."""
import json
import os
from functools import lru_cache

from fastapi import APIRouter, Response

router = APIRouter(prefix="/v1/meta", tags=["meta"])
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data")

ACTIVITY_TYPES = [
    {"key": "ishlab_chiqarish", "label": "Ishlab chiqarish"},
    {"key": "qishloq_xojaligi", "label": "Qishloq xo'jaligi"},
    {"key": "savdo", "label": "Savdo"},
    {"key": "xizmat", "label": "Xizmat ko'rsatish"},
]


@lru_cache
def _business_categories() -> dict:
    with open(os.path.join(DATA_DIR, "categories.json"), encoding="utf-8") as f:
        return json.load(f)


@router.get("/activity-types")
async def activity_types(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return ACTIVITY_TYPES


@router.get("/business-categories")
async def business_categories(response: Response):
    response.headers["Cache-Control"] = "public, max-age=3600"
    return _business_categories()
