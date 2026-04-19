"""Bulk-update the <header class="navbar">...</header> block on all frontend HTML pages
to the new icon-nav + top-search + category-strip structure (Batch A redesign).

Usage:  python scripts/update-nav.py

Idempotent: re-running on already-updated files is a no-op (the new marker
'<div class="category-strip">' is detected and skipped).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"

# Per-page configuration: filename -> active link key
# Active key matches the data-nav attribute we add to each <a>.
ACTIVE_MAP = {
    "index.html":     "shop",
    "product.html":   "shop",
    "cart.html":      "cart",
    "checkout.html":  "cart",
    "orders.html":    "orders",
    "wishlist.html":  "wishlist",
    "account.html":   "account",
    "login.html":     None,
    "callback.html":  None,
    "contact.html":   "about",
    "404.html":       None,
}

NAV_TEMPLATE = '''    <header class="navbar">
        <a href="index.html" class="logo">Shop<span>Cloud</span></a>
        <button class="hamburger" onclick="toggleMobileMenu()" aria-label="Menu"><span></span><span></span><span></span></button>
        <nav class="nav-links">
            <a href="index.html" data-nav="shop"{shop_active}>Shop All</a>
            <a href="index.html?filter=new" data-nav="new">New Arrivals</a>
            <a href="index.html?filter=best-sellers" data-nav="best">Best Sellers</a>
            <a href="contact.html" data-nav="about"{about_active}>About</a>
        </nav>
        <form class="nav-search" onsubmit="submitNavSearch(event)">
            <span class="search-glyph"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></span>
            <input type="text" id="nav-search-input" placeholder="Search products..." autocomplete="off">
        </form>
        <div class="nav-icons">
            <a href="orders.html" class="nav-icon-btn{orders_active}" title="Orders" aria-label="Orders"><svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg></a>
            <a href="wishlist.html" class="nav-icon-btn{wishlist_active}" title="Wishlist" aria-label="Wishlist"><svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg><span id="wishlist-badge" class="cart-badge" style="display:none">0</span></a>
            <a href="cart.html" class="nav-icon-btn cart-link{cart_active}" title="Cart" aria-label="Cart"><svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg><span id="cart-badge" class="cart-badge" style="display:none">0</span></a>
            <a href="account.html" class="nav-icon-btn{account_active}" id="account-link" title="Account" aria-label="Account" style="display:none"><svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></a>
            <a href="login.html" id="login-btn" class="btn btn-accent btn-sm" style="margin-left:8px;">Login</a>
            <a href="#" id="logout-btn" class="btn btn-outline btn-sm" style="display:none;margin-left:8px;" onclick="logout(); return false;">Logout</a>
        </div>
    </header>
    <div class="category-strip"><div class="category-strip-inner" id="category-strip"></div></div>'''


def render_nav(active_key: str | None) -> str:
    fields = {
        "shop_active":     ' class="active"' if active_key == "shop" else "",
        "about_active":    ' class="active"' if active_key == "about" else "",
        "orders_active":   " active" if active_key == "orders" else "",
        "wishlist_active": " active" if active_key == "wishlist" else "",
        "cart_active":     " active" if active_key == "cart" else "",
        "account_active":  " active" if active_key == "account" else "",
    }
    return NAV_TEMPLATE.format(**fields)


# Match the existing navbar block. Greedy across the <header>...</header> tag pair
# only, so we don't accidentally consume the rest of the page.
NAV_RE = re.compile(
    r'    <header class="navbar">.*?</header>',
    re.DOTALL,
)

# Match the existing category-strip if present (so we replace it with the canonical one,
# avoiding duplicate strips when re-running).
STRIP_RE = re.compile(
    r'\n?    <div class="category-strip">.*?</div></div>',
    re.DOTALL,
)


def update_file(path: Path) -> str:
    src = path.read_text(encoding="utf-8")
    if not NAV_RE.search(src):
        return f"SKIP {path.name} (no navbar block found)"

    active = ACTIVE_MAP.get(path.name)
    new_block = render_nav(active)

    # Remove any existing category-strip (idempotent re-run)
    src = STRIP_RE.sub("", src)
    # Replace the navbar block with the new navbar + category-strip
    new_src = NAV_RE.sub(new_block, src, count=1)

    if new_src == src:
        return f"NOOP {path.name}"
    path.write_text(new_src, encoding="utf-8")
    return f"OK   {path.name}"


def main():
    pages = sorted(FRONTEND.glob("*.html"))
    for p in pages:
        print(update_file(p))


if __name__ == "__main__":
    main()
