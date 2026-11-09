"""Backend OpenAPI sxemasini qayta eksport qilib, frontend/docs ga nusxalaydi.
Ishga tushirish (loyiha ildizidan): python scripts/sync_contract.py
Backend bog'liqliklari o'rnatilgan bo'lishi kerak (backend/requirements-dev.txt)."""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

env = {**os.environ, "PYTHONPATH": BACKEND}
subprocess.run([sys.executable, os.path.join(BACKEND, "scripts", "export_openapi.py")], cwd=BACKEND, env=env, check=True)
for name in ("openapi.json", "API_CONTRACT.md"):
    shutil.copyfile(os.path.join(BACKEND, "docs", name), os.path.join(ROOT, "frontend", "docs", name))
print("frontend/docs yangilandi")
