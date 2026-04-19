#!/usr/bin/env bash
# ShopCloud — Frontend/UI commits (~18 commits)
# Run by: FRONTEND TEAMMATE
#
# This is the THIRD script that runs (after Rasha pushed devops AND backend
# teammate pushed app commits). It pulls the latest, copies in source files
# from the zip Rasha sent, adds the frontend commits under YOUR git identity,
# and pushes.
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
#   7. bash commit-frontend.sh
#   8. git push origin main

set -e
cd "$(dirname "$0")"

# ── 13. Frontend core (HTML + JS + CSS) ──
git add frontend/index.html \
  frontend/product.html \
  frontend/cart.html \
  frontend/checkout.html \
  frontend/login.html \
  frontend/callback.html \
  frontend/orders.html \
  frontend/js/config.js \
  frontend/js/auth.js \
  frontend/js/api.js \
  frontend/js/catalog.js \
  frontend/js/cart.js \
  frontend/js/checkout.js \
  frontend/css/style.css
git commit -m "feat: add responsive frontend with hero, skeleton loading, multi-step checkout, order timeline, dev-mode auth, mobile hamburger, star ratings, promo bar, SVG trust icons, and Google Fonts (Inter)"

# ── 13b. Frontend extended features (account, wishlist, contact, 404) ──
git add frontend/account.html \
  frontend/wishlist.html \
  frontend/contact.html \
  frontend/404.html \
  frontend/js/account.js \
  frontend/js/wishlist.js
git commit -m "feat: add account management, wishlist, contact/FAQ, 404 page"

# ── 13c. Professional login/register page ──
git add frontend/login.html \
  frontend/js/auth.js \
  frontend/css/style.css
git commit -m "feat: professional sign-in/register with marketing hero, testimonial, category tags, member perks, Google login, password strength meter"

# ── 13d. Cancel order API + UI polish ──
git add app/services/checkout/router.py \
  app/services/checkout/service.py \
  app/entrypoints/combined.py \
  frontend/index.html \
  frontend/product.html \
  frontend/cart.html \
  frontend/checkout.html \
  frontend/orders.html \
  frontend/wishlist.html \
  frontend/account.html \
  frontend/contact.html \
  frontend/404.html \
  frontend/js/api.js \
  frontend/css/style.css
git commit -m "feat: functional cancel order API, SVG category icons, promo bar, professional footers, cleaned FAQ"

# ── 24. Frontend: coupon UI, reorder, sort + price filter, breakdown ──
git add frontend/index.html \
  frontend/checkout.html \
  frontend/orders.html \
  frontend/js/cart.js \
  frontend/js/catalog.js \
  frontend/js/checkout.js \
  frontend/css/style.css
git commit -m "feat(frontend): coupon flow, server-side sort, price range filter, reorder button, discount breakdown"

# ── 28. Self-host Inter font (no external CDN dependency) ──
git add frontend/fonts/inter-latin.woff2 \
  frontend/css/style.css
git commit -m "chore(frontend): self-host Inter variable font, drop Google Fonts CDN for 100% self-contained asset delivery"

# ── 29. Remove internal architecture/course disclosures from user-facing UI ──
git add frontend/404.html \
  frontend/callback.html \
  frontend/login.html \
  frontend/contact.html \
  frontend/js/account.js \
  frontend/js/auth.js \
  frontend/js/wishlist.js
git commit -m "chore(frontend): sanitize user-visible UI and source comments — remove AWS/Cognito/course-code references"

# ── 31. Frontend: premium storefront redesign wired to new catalog endpoints ──
git add frontend/index.html \
  frontend/product.html \
  frontend/cart.html \
  frontend/js/api.js \
  frontend/js/catalog.js \
  frontend/js/cart.js \
  frontend/css/style.css \
  frontend/media/
git commit -m "feat(frontend): hero carousel + flash banner (GET /api/promotions), best-sellers & new-arrivals rows, testimonials section, product image gallery, reviews UI with submission form, free-shipping progress bar, real star ratings from backend — all assets served by CloudFront via frontend/media/"

# ── 32. NOXA-style light theme + split hero + shop-by-category + newsletter band ──
git add frontend/index.html \
  frontend/css/style.css \
  frontend/js/api.js \
  app/scripts/seed_data.py \
  scripts/update-nav.py \
  frontend/account.html \
  frontend/cart.html \
  frontend/checkout.html \
  frontend/contact.html \
  frontend/login.html \
  frontend/orders.html \
  frontend/product.html \
  frontend/wishlist.html \
  frontend/callback.html \
  frontend/404.html
git commit -m "feat(frontend): NOXA-inspired light theme — cream/navy navbar, split-layout hero, shop-by-category cards, newsletter band, palette-aligned flash banner with functional CTA"

# ── 33. Wishlist polish — compact rows, prominent PDP heart, auto-remove on add-to-cart ──
git add frontend/js/wishlist.js \
  frontend/js/cart.js \
  frontend/product.html \
  frontend/css/style.css
git commit -m "feat(wishlist): compact row layout, prominent Save-to-Wishlist button on PDP (in & out of stock), silent auto-remove when item added to cart"

# ── 34. Saved addresses — editable in My Account, selectable on checkout ──
git add frontend/account.html \
  frontend/js/account.js \
  frontend/checkout.html \
  frontend/js/checkout.js \
  frontend/css/style.css
git commit -m "feat(addresses): edit saved addresses in My Account, address picker on checkout with default-auto-select and dedupe-on-save"

# ── 35. Past Orders tab + Men/Women clothing sub-filter ──
git add frontend/orders.html \
  frontend/js/catalog.js \
  app/scripts/seed_data.py \
  frontend/css/style.css
git commit -m "feat(orders+catalog): tabbed orders view (Active/Past/All) with counts, Men/Women sub-filter on Clothing category driven by Product.attributes.gender"

# ── 37. Optional checkout features — clothing sizes, payment method, min order ──
git add frontend/product.html \
  frontend/checkout.html \
  frontend/js/cart.js \
  frontend/js/checkout.js \
  frontend/css/style.css
git commit -m "feat(checkout): XS/S/M/L/XL size selector for clothing on PDP (persists with cart item), Cash-on-Delivery / Card payment selector with confirmation display, \$20 minimum order enforcement"

# ── 39. Single-page Cognito sign-in/up (no Hosted UI redirect) ──
git add frontend/js/auth.js \
  frontend/login.html \
  frontend/js/config.js \
  scripts/deploy-frontend.sh
git commit -m "feat(auth): single-page sign-in/up via direct Cognito API (InitiateAuth, SignUp, Confirm, ForgotPassword) — no Hosted UI redirect; deploy-frontend.sh callback port fixed (3000→CF domain)"

# ── 42. Catalog UX: stop scroll-to-top + product shrink on filter change ──
git add frontend/js/catalog.js \
  frontend/css/style.css
git commit -m "fix(catalog): no scroll-jump or visible reflow on category/gender/special-filter change — dim cards in place + scroll products section into view"

# ── 43b. Auth UX: persistent inline status banner + longer toast ──
git add frontend/login.html \
  frontend/js/api.js
git commit -m "fix(auth ux): persistent inline status banner under auth heading + toast 3s→5s — users were missing the transient toast and assuming sign-in/register did nothing"

# ── 43. Auth UX: kill last Hosted-UI escape hatches ──
git add frontend/js/auth.js \
  frontend/login.html
git commit -m "fix(auth): remove last two Hosted-UI redirects (redirectToLogin → login.html; hide Google social button — Google IdP not configured in prod) so users sign in once via the in-page form"

# ── 44. Orders UX: always-visible invoice button (generating / ready) ──
git add frontend/orders.html
git commit -m "feat(orders): always show invoice action with generating/ready/cancelled states + per-order refresh button (was hidden until invoice_url populated)"

# ── Catch any leftover frontend files ──
git add -A
git diff --cached --quiet || git commit -m "chore(frontend): include any remaining untracked frontend files"

echo ""
echo "== Frontend commits done =="
git log --oneline | head -30
