#!/usr/bin/env bash
# ShopCloud — Backend/App commits (9 commits)
# Run by: BACKEND TEAMMATE
#
# Usage:
#   1. Receive shopcloud-source.zip from Rasha and unzip it somewhere, e.g. ~/shopcloud-src
#   2. git clone https://github.com/ralphnasr/DevOps.git
#   3. cd DevOps
#   4. Copy ALL files from the unzipped source over this checkout
#      (Windows: xcopy /E /Y ..\shopcloud-src\*  .\
#       Mac/Linux: cp -R ../shopcloud-src/. .)
#   5. git config user.name  "Your Full Name"
#   6. git config user.email "your_github_email@example.com"   (MUST match your GitHub account email)
#   7. bash commit-backend.sh
#   8. git push origin main          (if rejected: git pull --rebase origin main, then push)

set -e
cd "$(dirname "$0")"

# ── 1. SQLAlchemy models, Pydantic schemas, Alembic config, initial migration ──
git add app/shared/__init__.py \
  app/shared/database.py \
  app/shared/config.py \
  app/shared/models.py \
  app/shared/schemas.py \
  app/alembic.ini \
  app/migrations/env.py \
  app/migrations/versions/001_initial_schema.py
git commit -m "feat(db): add SQLAlchemy models, Pydantic schemas, Alembic config, and initial migration (001)"

# ── 2. Cognito JWT auth + Redis client + FastAPI dependencies ──
git add app/shared/auth.py \
  app/shared/redis_client.py \
  app/shared/dependencies.py
git commit -m "feat(auth): Cognito JWT verification (customer + admin pools), Redis cart client, shared FastAPI dependencies"

# ── 3. Catalog service (listing, search, sort, filters, reviews, promotions, testimonials) ──
git add app/services/catalog/__init__.py \
  app/services/catalog/service.py \
  app/services/catalog/router.py \
  app/entrypoints/catalog.py \
  app/migrations/versions/003_reviews_promotions_media.py
git commit -m "feat(catalog): product listing/search/sort/price-filter, reviews with aggregate ratings, promotions (hero + flash), testimonials, image gallery (migration 003)"

# ── 4. Cart service (Redis-backed, server-side stock guard) ──
git add app/services/cart/__init__.py \
  app/services/cart/service.py \
  app/services/cart/router.py \
  app/entrypoints/cart.py
git commit -m "feat(cart): Redis-backed cart with add/update/remove and server-side stock guard on add and quantity update"

# ── 5. Checkout service (orders, coupons, reorder, async invoice via BackgroundTask) ──
git add app/services/checkout/__init__.py \
  app/services/checkout/service.py \
  app/services/checkout/router.py \
  app/entrypoints/checkout.py \
  app/shared/coupons.py \
  app/migrations/versions/002_coupons_audit_log.py
git commit -m "feat(checkout): order placement + history, coupon validation, reorder endpoint, cancel order, FastAPI BackgroundTask publishes invoice SQS message after response (migration 002 — coupons + audit log + order discount fields)"

# ── 6. Admin panel (Jinja2 templates, coupons CRUD, audit log, analytics) ──
git add app/services/admin/__init__.py \
  app/services/admin/service.py \
  app/services/admin/router.py \
  app/services/admin/templates/base.html \
  app/services/admin/templates/dashboard.html \
  app/services/admin/templates/products.html \
  app/services/admin/templates/product_form.html \
  app/services/admin/templates/orders.html \
  app/services/admin/templates/inventory.html \
  app/services/admin/templates/coupons.html \
  app/services/admin/templates/audit.html \
  app/services/admin/templates/analytics.html \
  app/entrypoints/admin.py
git commit -m "feat(admin): Jinja2 admin panel — dashboard, products, inventory, orders (status enum aligned with DB), coupons CRUD, audit log on all mutations, 30-day analytics; revenue excludes cancelled orders, Active Products requires stock>0"

# ── 7. Invoice Lambda pipeline (PDF + S3 + SES) ──
git add app/invoice/__init__.py \
  app/invoice/lambda_function.py \
  app/invoice/requirements.txt \
  app/migrations/versions/004_widen_invoice_url.py
git commit -m "feat(invoice): Lambda PDF generator → S3 → SES email; widen orders.invoice_url to TEXT (migration 004) — presigned S3 URLs exceeded VARCHAR(500)"

# ── 8. Combined dev entrypoint + seed data ──
git add app/entrypoints/combined.py \
  app/scripts/__init__.py \
  app/scripts/seed_data.py
git commit -m "feat(dev): combined FastAPI entrypoint for local development + seed_data.py (25 products, coupons, promotions, testimonials, Men/Women clothing attributes)"

# ── 9. Unit tests ──
git add app/tests/__init__.py \
  app/tests/conftest.py \
  app/tests/test_catalog.py \
  app/tests/test_cart.py \
  app/tests/test_checkout.py \
  app/tests/test_admin.py
git commit -m "test: unit tests for catalog, cart, checkout, and admin services (32/32 passing) with NullPool conftest for SQLite per-test isolation"

# ── Catch any leftover backend files (defensive) ──
git add -A
git diff --cached --quiet || git commit -m "chore(backend): include any remaining untracked backend files"

echo ""
echo "== Backend commits done =="
git log --oneline | head -25
