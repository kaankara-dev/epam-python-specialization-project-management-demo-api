# ---- Aşama 1: Builder ----
FROM python:3.12-slim AS builder

# uv'yi kur (bağımlılık çözümleme ve kurulum için)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# ÖNEMLİ: Önce sadece bağımlılık dosyalarını kopyala, kodu değil.
# Bu, Docker'ın "layer caching" mekanizmasından faydalanmak için.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Şimdi asıl kodu kopyala
COPY app/ ./app/

# ---- Aşama 2: Final (runtime) ----
FROM python:3.12-slim

WORKDIR /app

# Builder'dan sadece kurulu paketleri ve kodu al, uv'nin kendisini ALMA
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]