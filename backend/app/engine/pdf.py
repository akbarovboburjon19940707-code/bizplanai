"""Word -> PDF: LibreOffice (soffice) headless. Worker'da, reja yaratilgandan keyin.

PDF qo'shimcha format: konvertatsiya bo'lmasa (soffice yo'q, vaqt tugadi, xato) None qaytadi va reja
Word + Excel bilan baribir tayyor bo'ladi.
"""
import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

from app.core.config import get_settings

log = logging.getLogger(__name__)
_semaphore: asyncio.Semaphore | None = None


def soffice_binary() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def _limit() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        _semaphore = asyncio.Semaphore(max(1, get_settings().pdf_concurrency))
    return _semaphore


async def docx_to_pdf(docx_path: str, out_dir: str) -> str | None:
    """`docx_path` ni `out_dir` ga PDF qiladi. Muvaffaqiyatda PDF yo'li, aks holda None (xato loglanadi)."""
    s = get_settings()
    binary = soffice_binary()
    if not s.pdf_enabled or not binary:
        return None
    target = Path(out_dir) / (Path(docx_path).stem + ".pdf")
    async with _limit():
        # Har konvertatsiya o'z profilida: parallel soffice'lar bir-birini qulflamaydi
        with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile:
            proc = await asyncio.create_subprocess_exec(
                binary, "--headless", "--norestore", "--nolockcheck", f"-env:UserInstallation=file://{profile}",
                "--convert-to", "pdf", "--outdir", out_dir, docx_path,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "HOME": profile},
            )
            try:
                _, err = await asyncio.wait_for(proc.communicate(), timeout=s.pdf_timeout_seconds)
            except TimeoutError:
                proc.kill()
                await proc.wait()
                log.warning("PDF: soffice %s s ichida tugamadi", s.pdf_timeout_seconds)
                return None
    if proc.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
        log.warning("PDF: konvertatsiya xatosi (kod %s): %s", proc.returncode, err.decode(errors="replace")[-300:])
        return None
    return str(target)
