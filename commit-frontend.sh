#!/usr/bin/env bash
# ShopCloud — Frontend/UI commits (10 commits)
# Run by: FRONTEND TEAMMATE
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
#   8. git push origin main          (if rejected: git pull --rebase origin main, then push)

set -e
cd "$(dirname "$0")"

# ── 1. Core HTML pages (storefront, product, cart, checkout, login, callback, orders) ──
git add frontend/index.html \
  frontend/product.html \
  frontend/cart.html \
  frontend/checkout.html \
  frontend/login.html \
  frontend/callback.html \
  frontend/orders.html
git commit -m "feat(frontend): core HTML — homepage with split hero + shop-by-category + featured rows + testimonials + newsletter band, product detail page with image gallery + reviews + size selector, cart, multi-step checkout (shipping → payment → confirm), tabbed orders view (Active/Past/All) with always-visible invoice action, login/register, OAuth callback"

# ── 2. Account, wishlist, contact, 404 pages ──
git add frontend/account.html \
  frontend/wishlist.html \
  frontend/contact.html \
  frontend/404.html
git commit -m "feat(frontend): account dashboard with editable saved addresses, wishlist with compact rows, contact/FAQ, branded 404"

# ── 3. Frontend config + Cognito direct sign-in/up ──
git add frontend/js/config.js \
  frontend/js/auth.js
git commit -m "feat(auth): single-page sign-in/up via direct Cognito API (InitiateAuth, SignUp, ConfirmSignUp, ResendCode, ForgotPassword) — no Hosted UI redirect; dev-login locked to localhost; Google IdP button hidden (not configured in prod)"

# ── 4. API client (toasts, persistent inline status banner, mobile hamburger, back-to-top) ──
git add frontend/js/api.js
git commit -m "feat(frontend): API client + toast notifications (5s duration), persistent inline status banner under auth heading, mobile hamburger menu, back-to-top button, cart badge updater"

# ── 5. Catalog JS (sort, price filter, category cards, gender sub-filter, no scroll-jump) ──
git add frontend/js/catalog.js
git commit -m "feat(catalog): server-side sort + min/max price filter, skeleton loading, Men/Women sub-filter on Clothing (driven by Product.attributes.gender), no scroll-jump or visible reflow on filter change (dim cards in place + smooth scroll)"

# ── 6. Cart JS (add/update/remove, coupon flow, free-shipping bar, size persistence) ──
git add frontend/js/cart.js
git commit -m "feat(cart): add/update/remove with discount breakdown, coupon application, free-shipping progress bar, XS/S/M/L/XL size persists with cart item, silent auto-remove from wishlist when added"

# ── 7. Checkout JS (multi-step, shipping form, address picker, payment selector, min order) ──
git add frontend/js/checkout.js
git commit -m "feat(checkout): multi-step flow (Cart → Shipping → Confirm), saved-address picker with default-auto-select + dedupe, Cash-on-Delivery / Card payment selector, \$20 minimum order enforcement, coupon validation"

# ── 8. Account JS + wishlist JS ──
git add frontend/js/account.js \
  frontend/js/wishlist.js
git commit -m "feat(frontend): account dashboard logic (orders summary, saved addresses CRUD), wishlist with prominent PDP heart and silent auto-remove on add-to-cart"

# ── 9. NOXA-inspired stylesheet (light theme, hero, cards, footer, responsive, skeleton) ──
git add frontend/css/style.css
git commit -m "feat(frontend): NOXA-inspired light theme stylesheet — cream/navy navbar, split-layout hero, shop-by-category cards, multi-column footer, newsletter band, skeleton loading shimmer, responsive 768/480 breakpoints, hamburger drawer, real star ratings, free-shipping progress bar, address picker, payment selector"

# ── 10. Self-hosted Inter font + media assets ──
git add frontend/fonts/inter-latin.woff2 \
  frontend/media/ \
  scripts/update-nav.py
git commit -m "chore(frontend): self-host Inter variable font (drop Google Fonts CDN), product/promo media assets served from CloudFront via frontend/media/, update-nav.py helper script"

# ── Catch any leftover frontend files (defensive) ──
git add -A
git diff --cached --quiet || git commit -m "chore(frontend): include any remaining untracked frontend files"

echo ""
echo "== Frontend commits done =="
git log --oneline | head -30
