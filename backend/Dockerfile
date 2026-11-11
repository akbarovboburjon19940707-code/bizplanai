FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# Reja PDF'i (Word -> PDF, worker'da): LibreOffice Writer va shriftlar. Liberation = Times New Roman / Arial,
# Carlito = Calibri bilan bir xil o'lchamli (sahifalar Word'dagidek bo'linadi)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libreoffice-writer-nogui fonts-liberation fonts-crosextra-carlito fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN useradd --create-home --uid 10001 app && chown -R app /app
USER app

# Render PORT ni beradi. --proxy-headers: haqiqiy mijoz IP si rate limit uchun.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers ${WEB_CONCURRENCY:-2} \
    --proxy-headers --forwarded-allow-ips='*' --no-server-header
