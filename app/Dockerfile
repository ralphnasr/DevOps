# ── Base stage: shared dependencies ──
FROM python:3.12-slim AS base
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared/ shared/
COPY services/ services/

# Run as non-root (uid 1000). Required by AWS Config rule
# ECS_TASK_DEFINITION_NONROOT_USER and a general security best practice —
# running app code as root inside a container is unnecessary and increases
# blast radius if the container is ever compromised.
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# ── Catalog service ──
FROM base AS catalog
COPY entrypoints/catalog.py .
EXPOSE 8000
CMD ["uvicorn", "catalog:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Cart service ──
FROM base AS cart
COPY entrypoints/cart.py .
EXPOSE 8000
CMD ["uvicorn", "cart:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Checkout service ──
FROM base AS checkout
COPY entrypoints/checkout.py .
EXPOSE 8000
CMD ["uvicorn", "checkout:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Admin service ──
FROM base AS admin
COPY entrypoints/admin.py .
COPY services/admin/templates/ templates/
EXPOSE 8000
CMD ["uvicorn", "admin:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Migration runner ──
FROM base AS migrate
COPY alembic.ini .
COPY migrations/ migrations/
COPY scripts/ scripts/
CMD ["alembic", "upgrade", "head"]

# ── Combined (dev only) ──
FROM base AS combined
COPY entrypoints/combined.py .
EXPOSE 8000
CMD ["uvicorn", "combined:app", "--host", "0.0.0.0", "--port", "8000"]
