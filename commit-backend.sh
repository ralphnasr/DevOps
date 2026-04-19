#!/usr/bin/env bash
# ShopCloud — Backend/App commits (~17 commits)
# Run by: BACKEND TEAMMATE
#
# This is the SECOND script that runs (after Rasha pushed devops commits).
# It clones the repo, copies in source files from the zip Rasha sent,
# adds the backend commits under YOUR git identity, and pushes.
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
#   8. git push origin main

set -e
cd "$(dirname "$0")"

# ── 3. Shared application modules ──
git add app/shared/__init__.py \
  app/shared/config.py \
  app/shared/database.py \
  app/shared/models.py \
  app/shared/schemas.py \
  app/shared/auth.py \
  app/shared/redis_client.py \
  app/shared/dependencies.py
git commit -m "feat: add shared modules (config, database, models, schemas, auth, redis, dependencies)"

# ── 4. Database migration + Alembic config ──
git add app/alembic.ini \
  app/migrations/env.py \
  app/migrations/versions/001_initial_schema.py
git commit -m "feat: add Alembic config and initial database migration"

# ── 5. Catalog service ──
git add app/services/catalog/__init__.py \
  app/services/catalog/service.py \
  app/services/catalog/router.py \
  app/entrypoints/catalog.py
git commit -m "feat: add catalog service (product listing, search, categories)"

# ── 6. Cart service ──
git add app/services/cart/__init__.py \
  app/services/cart/service.py \
  app/services/cart/router.py \
  app/entrypoints/cart.py
git commit -m "feat: add cart service (Redis-backed cart with add, update, remove)"

# ── 7. Checkout service ──
git add app/services/checkout/__init__.py \
  app/services/checkout/service.py \
  app/services/checkout/router.py \
  app/entrypoints/checkout.py
git commit -m "feat: add checkout service (order placement, history, SQS integration)"

# ── 8. Admin service + templates ──
git add app/services/admin/__init__.py \
  app/services/admin/service.py \
  app/services/admin/router.py \
  app/services/admin/templates/base.html \
  app/services/admin/templates/dashboard.html \
  app/services/admin/templates/products.html \
  app/services/admin/templates/product_form.html \
  app/services/admin/templates/orders.html \
  app/services/admin/templates/inventory.html \
  app/entrypoints/admin.py
git commit -m "feat: add admin panel with Jinja2 templates (dashboard, products, orders, inventory)"

# ── 9. Combined entrypoint + seed data ──
git add app/entrypoints/combined.py \
  app/scripts/__init__.py \
  app/scripts/seed_data.py
git commit -m "feat: add combined dev entrypoint and seed data script"

# ── 10. Invoice Lambda pipeline ──
git add app/invoice/__init__.py \
  app/invoice/lambda_function.py \
  app/invoice/requirements.txt
git commit -m "feat: add Lambda invoice pipeline (PDF generation, S3 storage, SES email)"

# ── 11. Unit tests ──
git add app/tests/__init__.py \
  app/tests/conftest.py \
  app/tests/test_catalog.py \
  app/tests/test_cart.py \
  app/tests/test_checkout.py \
  app/tests/test_admin.py
git commit -m "test: add unit tests for catalog, cart, checkout, and admin services"

# ── 18. Audit fix: admin order status enum ──
git add app/services/admin/service.py \
  app/services/admin/templates/orders.html
git commit -m "fix: align admin order status enum with DB constraint (pending → processing)"

# ── 20. Migration: coupons, audit log, order discount fields ──
git add app/shared/models.py \
  app/shared/schemas.py \
  app/shared/coupons.py \
  app/migrations/versions/002_coupons_audit_log.py
git commit -m "feat(db): add Coupon and AuditLog models, order discount fields, migration 002"

# ── 21. Catalog: server-side sort + price range filters ──
git add app/services/catalog/service.py \
  app/services/catalog/router.py
git commit -m "feat(catalog): add server-side sort, min/max price filters, price-range endpoint"

# ── 22. Checkout: coupon validation + reorder endpoint ──
git add app/services/checkout/service.py \
  app/services/checkout/router.py
git commit -m "feat(checkout): apply coupons at checkout, add /coupons/validate and /orders/{id}/reorder"

# ── 23. Admin: coupons, audit log, analytics dashboard ──
git add app/services/admin/service.py \
  app/services/admin/router.py \
  app/services/admin/templates/base.html \
  app/services/admin/templates/coupons.html \
  app/services/admin/templates/audit.html \
  app/services/admin/templates/analytics.html
git commit -m "feat(admin): add coupons CRUD, audit log on all mutations, 30-day analytics dashboard"

# ── 30. Backend: reviews, promotions, testimonials, product media + rating columns ──
git add app/shared/models.py \
  app/shared/schemas.py \
  app/services/catalog/router.py \
  app/services/catalog/service.py \
  app/entrypoints/catalog.py \
  app/entrypoints/combined.py \
  app/migrations/versions/003_reviews_promotions_media.py \
  app/scripts/seed_data.py
git commit -m "feat(catalog): reviews (with aggregate ratings), promotions (hero + flash slots), testimonials, product image gallery + sales_count — mapped to existing RDS; no new AWS services"

# ── 36. Admin compliance fixes (revenue, edit 404, active count, stock guard) ──
git add app/services/admin/service.py \
  app/services/admin/router.py \
  app/services/cart/service.py \
  app/services/cart/router.py
git commit -m "fix(admin+cart): exclude cancelled orders from revenue, fix Edit Product 404 (direct lookup vs paginated scan), Active Products count requires stock>0, server-side stock guard on cart add and quantity update"

# ── 45. Async invoice: SQS publish moves to FastAPI BackgroundTask ──
git add app/services/checkout/service.py \
  app/services/checkout/router.py \
  app/tests/test_checkout.py
git commit -m "feat(checkout): publish invoice SQS message via FastAPI BackgroundTask so /api/checkout returns immediately and the customer can keep shopping while invoice generation runs out of band"

# ── Catch any leftover backend files ──
git add -A
git diff --cached --quiet || git commit -m "chore(backend): include any remaining untracked backend files"

echo ""
echo "== Backend commits done =="
git log --oneline | head -25
