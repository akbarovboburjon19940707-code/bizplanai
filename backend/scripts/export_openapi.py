"""OpenAPI sxemasini docs/openapi.json ga yozadi (frontend TypeScript tiplari shundan generatsiya qilinadi)."""
import json
import os

from app.main import app

out = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(app.openapi(), f, ensure_ascii=False, indent=2)
print(out)
