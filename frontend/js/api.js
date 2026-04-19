const api = {
    async _fetch(path, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${path}`;
        const headers = options.headers || {};
        headers["Content-Type"] = headers["Content-Type"] || "application/json";

        const token = await getValidToken();
        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const resp = await fetch(url, { ...options, headers });

        if (resp.status === 401) {
            clearTokens();
            throw new Error("Please log in to continue");
        }

        if (!resp.ok) {
            const error = await resp.json().catch(() => ({ detail: "Request failed" }));
            throw new Error(error.detail || `HTTP ${resp.status}`);
        }

        return resp.json();
    },

    get(path) { return this._fetch(path, { method: "GET" }); },
    post(path, body) { return this._fetch(path, { method: "POST", body: JSON.stringify(body) }); },
    put(path, body) { return this._fetch(path, { method: "PUT", body: JSON.stringify(body) }); },
    patch(path, body) { return this._fetch(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }); },
    delete(path) { return this._fetch(path, { method: "DELETE" }); },
};

/* ══════════════════════════════════════════════════
   Category Helpers
   ══════════════════════════════════════════════════ */
function getCategorySlug(name) {
    const map = { "Electronics": "electronics", "Clothing": "clothing", "Home & Kitchen": "home", "Sports & Outdoors": "sports", "Books": "books", "Beauty & Health": "beauty" };
    return map[name] || "default";
}

function getCategoryIcon(name) {
    const icons = {
        "Electronics": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="12" y1="18" x2="12" y2="18"/></svg>',
        "Clothing": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2l3 4h6l3-4"/><path d="M6 2C4 3 2 6 2 8l4 2v12h12V10l4-2c0-2-2-5-4-6"/></svg>',
        "Home & Kitchen": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "Sports & Outdoors": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
        "Books": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
        "Beauty & Health": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'
    };
    return icons[name] || '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>';
}

function getCategoryPlaceholderIcon(name) {
    const icons = {
        "Electronics": '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
        "Clothing": '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><path d="M6 2l3 4h6l3-4"/><path d="M6 2C4 3 2 6 2 8l4 2v12h12V10l4-2c0-2-2-5-4-6"/></svg>',
        "Home & Kitchen": '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "Sports & Outdoors": '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
        "Books": '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
        "Beauty & Health": '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'
    };
    return icons[name] || '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.85)" stroke-width="1.5"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>';
}

function primaryImage(product) {
    if (product.images && product.images.length) return product.images[0];
    return product.image_url || null;
}

function productImageHtml(product, height) {
    const h = height || 220;
    const cat = product.category ? product.category.name : "";
    const src = primaryImage(product);
    if (src) {
        return `<img src="${src}" alt="${product.name}" style="height:${h}px;" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
                <div class="product-placeholder ph-${getCategorySlug(cat)}" style="display:none;height:${h}px;">
                    <span class="ph-icon">${getCategoryPlaceholderIcon(cat)}</span>
                    <span class="ph-label">${cat}</span>
                </div>`;
    }
    return `<div class="product-placeholder ph-${getCategorySlug(cat)}" style="height:${h}px;">
                <span class="ph-icon">${getCategoryPlaceholderIcon(cat)}</span>
                <span class="ph-label">${cat}</span>
            </div>`;
}

/* Star Rating — prefer product.avg_rating + product.review_count */
function getProductRating(product) {
    if (product && typeof product === "object" && product.avg_rating != null) {
        return { rating: Number(product.avg_rating) || 0, count: product.review_count || 0 };
    }
    const id = typeof product === "number" ? product : (product && product.id) || 0;
    const seed = ((id * 2654435761) >>> 0) % 100;
    const rating = 3.5 + (seed / 100) * 1.5;
    const count = 10 + (seed % 90);
    return { rating: Math.round(rating * 10) / 10, count };
}

function renderStars(rating) {
    let html = '<div class="star-rating">';
    for (let i = 1; i <= 5; i++) {
        if (i <= Math.floor(rating)) {
            html += '<span>&#9733;</span>';
        } else if (i - 0.5 <= rating) {
            html += '<span>&#9733;</span>';
        } else {
            html += '<span class="star-empty">&#9733;</span>';
        }
    }
    html += '</div>';
    return html;
}

/* ══════════════════════════════════════════════════
   Reusable Product Card
   ══════════════════════════════════════════════════ */
function renderProductCard(product, index) {
    // Stagger removed — staggered animation-delay made the grid look like a wave
    // of cards expanding into place every time products refetched.
    const delay = 0;
    const catName = product.category ? product.category.name : "";
    const { rating, count } = getProductRating(product);

    let badges = "";
    if (catName) badges += `<span class="card-badge card-badge-category">${catName}</span>`;
    if (product.stock_quantity === 0) badges += `<span class="card-badge card-badge-out">Out of stock</span>`;
    else if (product.stock_quantity < 10) badges += `<span class="card-badge card-badge-low">Only ${product.stock_quantity} left</span>`;

    const wishlistBtn = (typeof wishlistButtonHtml === "function") ? wishlistButtonHtml(product.id) : "";

    return `
    <div class="product-card fade-in-up" style="animation-delay:${delay}s" onclick="window.location.href='product.html?id=${product.id}'">
        <div class="card-badges">${badges}</div>
        ${wishlistBtn}
        <div class="product-image">
            ${productImageHtml(product)}
            <div class="card-overlay">
                <button class="btn btn-white btn-sm" onclick="event.stopPropagation(); addToCart(${product.id})">Add to Cart</button>
                <button class="btn btn-outline btn-sm" style="color:#fff;border-color:rgba(255,255,255,.6)" onclick="event.stopPropagation(); window.location.href='product.html?id=${product.id}'">View Details</button>
            </div>
        </div>
        <div class="product-info">
            <p class="product-category">${catName}</p>
            <h3>${product.name}</h3>
            <div class="product-rating">${renderStars(rating)}<span class="rating-count">(${count})</span></div>
            <p class="product-price">$${product.price.toFixed(2)}</p>
            <p class="product-stock ${product.stock_quantity < 10 ? 'low-stock' : ''}">
                ${product.stock_quantity > 0 ? product.stock_quantity + ' in stock' : 'Out of stock'}
            </p>
        </div>
    </div>`;
}

/* ══════════════════════════════════════════════════
   Skeleton Loading
   ══════════════════════════════════════════════════ */
function showSkeletonCards(container, count) {
    const n = count || 8;
    let html = "";
    // Skeleton card height tuned to match real product card height
    // (220 image + ~140 info) so swap-in does not visibly shift the page.
    for (let i = 0; i < n; i++) {
        html += `<div class="skeleton-card" style="min-height:360px;">
            <div class="skeleton skeleton-image"></div>
            <div class="skeleton skeleton-line" style="width:40%;margin:16px 16px 0;height:11px;"></div>
            <div class="skeleton skeleton-line" style="width:80%;margin:10px 16px;height:16px;"></div>
            <div class="skeleton skeleton-line" style="width:55%;margin:8px 16px;height:14px;"></div>
            <div class="skeleton skeleton-line" style="width:35%;margin:8px 16px;height:20px;"></div>
            <div class="skeleton skeleton-line" style="width:30%;margin:8px 16px 16px;height:12px;"></div>
        </div>`;
    }
    container.innerHTML = html;
}

/* ══════════════════════════════════════════════════
   Toast Notifications
   ══════════════════════════════════════════════════ */
function showToast(message, type) {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type || "info"}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function showLoading(container) {
    container.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';
}

function showError(container, message) {
    container.innerHTML = `<div class="error-message">${message}</div>`;
}

/* ══════════════════════════════════════════════════
   Cart Badge (centralized)
   ══════════════════════════════════════════════════ */
async function updateCartBadge() {
    const badge = document.getElementById("cart-badge");
    if (!badge) return;
    try {
        const cart = await api.get("/api/cart");
        const count = cart.items ? cart.items.reduce((sum, i) => sum + i.quantity, 0) : 0;
        badge.textContent = count;
        badge.style.display = count > 0 ? "inline" : "none";
    } catch (e) {
        badge.style.display = "none";
    }
}

/* ══════════════════════════════════════════════════
   Mobile Menu
   ══════════════════════════════════════════════════ */
function toggleMobileMenu() {
    const nav = document.querySelector(".navbar .nav-links");
    const overlay = document.getElementById("mobile-overlay");
    if (nav) nav.classList.toggle("mobile-open");
    if (overlay) overlay.classList.toggle("show");
}

function closeMobileMenu() {
    const nav = document.querySelector(".navbar .nav-links");
    const overlay = document.getElementById("mobile-overlay");
    if (nav) nav.classList.remove("mobile-open");
    if (overlay) overlay.classList.remove("show");
}

/* ══════════════════════════════════════════════════
   Top Nav Search (always visible) — redirects to catalog with ?q=
   ══════════════════════════════════════════════════ */
function submitNavSearch(e) {
    if (e) e.preventDefault();
    const input = document.getElementById("nav-search-input");
    if (!input) return false;
    const q = (input.value || "").trim();
    if (!q) return false;
    // If already on index, run catalog search; otherwise navigate.
    const onIndex = /\/index\.html$|\/$/.test(location.pathname) || location.pathname.endsWith("/");
    if (onIndex && typeof loadProducts === "function") {
        if (typeof currentCategory !== "undefined") currentCategory = null;
        if (typeof currentSearch !== "undefined") currentSearch = q;
        const inlineInput = document.getElementById("search-input");
        if (inlineInput) inlineInput.value = q;
        loadProducts(1, null, q);
        const target = document.getElementById("products");
        if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
        location.href = `index.html?q=${encodeURIComponent(q)}#products`;
    }
    return false;
}

/* ══════════════════════════════════════════════════
   Category Strip (top of every page) — populated from /api/products/categories
   ══════════════════════════════════════════════════ */
async function loadCategoryStrip() {
    const container = document.getElementById("category-strip");
    if (!container) return;
    try {
        const categories = await api.get("/api/products/categories");
        const params = new URLSearchParams(location.search);
        const activeCat = params.get("category");
        let html = `<a href="index.html" class="${!activeCat ? 'active' : ''}">All</a>`;
        categories.forEach(cat => {
            const isActive = activeCat && Number(activeCat) === cat.id;
            html += `<a href="index.html?category=${cat.id}#products" class="${isActive ? 'active' : ''}" data-cat-id="${cat.id}">${getCategoryIcon(cat.name)}<span>${cat.name}</span></a>`;
        });
        container.innerHTML = html;
    } catch (e) {
        // Strip is non-critical; hide on failure
        const wrap = container.parentElement;
        if (wrap) wrap.style.display = "none";
    }
}

/* ══════════════════════════════════════════════════
   Shop-by-Category cards (homepage hero band)
   ══════════════════════════════════════════════════ */
function getCategoryCardIcon(name) {
    const icons = {
        "Electronics": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/></svg>',
        "Clothing":    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 2l3 4h6l3-4"/><path d="M6 2C4 3 2 6 2 8l4 2v12h12V10l4-2c0-2-2-5-4-6"/></svg>',
        "Home & Kitchen": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "Sports & Outdoors": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/></svg>',
        "Books":       '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
        "Beauty & Health": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>'
    };
    return icons[name] || '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/></svg>';
}

async function loadCategoryCards() {
    const container = document.getElementById("category-cards");
    if (!container) return;
    try {
        const categories = await api.get("/api/products/categories");
        // On the storefront (index.html) call filterByCategory directly — no page
        // reload, no flash of hero, no skeleton swap. Other pages fall back to a
        // proper href.
        const onIndex = !!document.getElementById("products-grid");
        container.innerHTML = categories.slice(0, 5).map(cat => onIndex ? `
            <a href="#products" class="cat-card" data-cat-id="${cat.id}" onclick="event.preventDefault(); filterByCategory(${cat.id}, null);">
                <span class="cat-card-icon">${getCategoryCardIcon(cat.name)}</span>
                <span class="cat-card-label">${cat.name}</span>
            </a>
        ` : `
            <a href="index.html?category=${cat.id}#products" class="cat-card">
                <span class="cat-card-icon">${getCategoryCardIcon(cat.name)}</span>
                <span class="cat-card-label">${cat.name}</span>
            </a>
        `).join("");
    } catch (e) {
        const section = document.getElementById("shop-by-category-section");
        if (section) section.style.display = "none";
    }
}

/* ══════════════════════════════════════════════════
   Back to Top
   ══════════════════════════════════════════════════ */
window.addEventListener("scroll", function () {
    const btn = document.getElementById("back-to-top");
    if (btn) btn.classList.toggle("visible", window.scrollY > 300);
});

/* ══════════════════════════════════════════════════
   Promo Bar Persistence + Category Strip auto-init
   ══════════════════════════════════════════════════ */
document.addEventListener("DOMContentLoaded", function () {
    const promo = document.getElementById("promo-bar");
    if (promo && localStorage.getItem("promo_dismissed") === "1") {
        promo.style.display = "none";
    }
    // Auto-load category strip on every page that includes it (idempotent —
    // index.html may also call this directly; loadCategoryStrip is safe to re-run).
    if (document.getElementById("category-strip")) {
        loadCategoryStrip();
    }
});
