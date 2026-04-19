let currentSort = "newest";
let currentProducts = [];
let currentCategory = null;
let currentSearch = null;
let currentMinPrice = null;
let currentMaxPrice = null;
let currentSpecialFilter = null; // 'new' | 'best-sellers' | 'featured' | null
let currentGender = null;        // 'men' | 'women' | null  (clothing sub-filter)

const CLOTHING_CATEGORY_ID = 2;

// Apply ?filter, ?category, ?q, ?gender from URL on load
function applyUrlFilters() {
    const params = new URLSearchParams(location.search);
    const filter = params.get("filter");
    const cat = params.get("category");
    const q = params.get("q");
    const gender = params.get("gender");
    if (filter && ["new", "best-sellers", "featured"].includes(filter)) {
        currentSpecialFilter = filter;
        if (filter === "new") currentSort = "newest";
    }
    if (cat) currentCategory = parseInt(cat, 10);
    if (gender && ["men", "women"].includes(gender)) currentGender = gender;
    if (q) {
        currentSearch = q;
        const inline = document.getElementById("search-input");
        if (inline) inline.value = q;
        const navInput = document.getElementById("nav-search-input");
        if (navInput) navInput.value = q;
    }
}

const SORT_MAP = {
    "default": "newest",
    "price-asc": "price_asc",
    "price-desc": "price_desc",
    "name-asc": "name_asc",
    "newest": "newest",
};

async function loadProducts(page, category, search) {
    if (page === undefined) page = 1;
    if (category !== undefined) currentCategory = category;
    if (search !== undefined) currentSearch = search;

    const container = document.getElementById("products-grid");
    // If grid already has product cards, dim them in place instead of replacing
    // with skeletons (prevents layout collapse + scroll-to-top jump on filter clicks).
    const hasExistingCards = container && container.querySelector(".product-card");
    if (hasExistingCards) {
        container.style.opacity = "0.5";
        container.style.pointerEvents = "none";
    } else {
        showSkeletonCards(container, 9);
    }

    const sortParam = SORT_MAP[currentSort] || "newest";

    try {
        let path, data;
        // Special filters from URL — Best Sellers / New Arrivals / Featured
        if (currentSpecialFilter && page === 1 && !currentSearch && !currentCategory && currentMinPrice == null && currentMaxPrice == null) {
            if (currentSpecialFilter === "best-sellers") {
                const items = await api.get("/api/products/best-sellers?limit=24");
                data = { items: items || [], total: (items || []).length, pages: 1, page: 1 };
            } else if (currentSpecialFilter === "new") {
                const items = await api.get("/api/products/new-arrivals?limit=24");
                data = { items: items || [], total: (items || []).length, pages: 1, page: 1 };
            } else if (currentSpecialFilter === "featured") {
                data = await api.get("/api/products?page=1&per_page=24&sort=newest");
            }
        } else {
            const params = new URLSearchParams({ page: String(page), per_page: "12", sort: sortParam });
            if (currentCategory) params.set("category_id", String(currentCategory));
            if (currentMinPrice != null && currentMinPrice !== "") params.set("min_price", String(currentMinPrice));
            if (currentMaxPrice != null && currentMaxPrice !== "") params.set("max_price", String(currentMaxPrice));
            if (currentSearch) params.set("q", currentSearch);

            path = currentSearch ? `/api/products/search?${params.toString()}` : `/api/products?${params.toString()}`;
            data = await api.get(path);
        }

        currentProducts = data.items || [];

        // Client-side gender filter for Clothing (attributes.gender is a JSONB field)
        if (currentCategory === CLOTHING_CATEGORY_ID && currentGender) {
            currentProducts = currentProducts.filter(p => p.attributes && p.attributes.gender === currentGender);
        }

        const countEl = document.getElementById("product-count");
        const shown = currentProducts.length;
        if (countEl) countEl.textContent = `${shown} product${shown !== 1 ? "s" : ""}`;

        renderGenderSubtabs();
        updateActiveFilters();
        renderProductCards(currentProducts);
        renderPagination(data);
        container.style.opacity = "";
        container.style.pointerEvents = "";
    } catch (e) {
        container.style.opacity = "";
        container.style.pointerEvents = "";
        showError(container, "Failed to load products. Please try again.");
    }
}

function renderGenderSubtabs() {
    let bar = document.getElementById("gender-subtabs");
    const isClothing = currentCategory === CLOTHING_CATEGORY_ID;
    if (!isClothing) {
        if (bar) bar.remove();
        return;
    }
    if (!bar) {
        const anchor = document.getElementById("products");
        const title = anchor ? anchor.querySelector(".section-title") : null;
        bar = document.createElement("div");
        bar.id = "gender-subtabs";
        bar.className = "gender-subtabs";
        if (title && title.parentNode) title.parentNode.insertBefore(bar, title.nextSibling);
    }
    bar.innerHTML = `
        <button type="button" class="gender-subtab ${!currentGender ? 'active' : ''}" onclick="setGenderFilter(null)">All</button>
        <button type="button" class="gender-subtab ${currentGender === 'men' ? 'active' : ''}" onclick="setGenderFilter('men')">Men</button>
        <button type="button" class="gender-subtab ${currentGender === 'women' ? 'active' : ''}" onclick="setGenderFilter('women')">Women</button>`;
}

function setGenderFilter(gender) {
    currentGender = gender;
    const url = new URL(location.href);
    if (gender) url.searchParams.set("gender", gender);
    else url.searchParams.delete("gender");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
    loadProducts(1);
    _scrollToProducts();
}

function clearSpecialFilter() {
    currentSpecialFilter = null;
    // Strip ?filter from URL without reload
    const url = new URL(location.href);
    url.searchParams.delete("filter");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
    // Restore the top-of-page sections that the special-filter mode hid
    _restoreTopSections();
    loadProducts(1);
}

/* In-page navbar/View-more filter switch — replaces full-reload <a href="?filter=…">
   so the user never sees the page bounce back to the hero and back. */
function applySpecialFilter(name) {
    if (!name || !["new", "best-sellers", "featured"].includes(name)) {
        clearSpecialFilter();
        return;
    }
    currentSpecialFilter = name;
    currentCategory = null;
    currentSearch = null;
    currentMinPrice = null;
    currentMaxPrice = null;
    currentGender = null;
    if (name === "new") currentSort = "newest";
    const url = new URL(location.href);
    url.searchParams.set("filter", name);
    url.searchParams.delete("category");
    url.searchParams.delete("q");
    history.replaceState(null, "", url.pathname + url.search + url.hash);
    _hideTopSections();
    document.querySelectorAll(".category-link").forEach(a => a.classList.remove("active"));
    const allLink = document.querySelector(".category-link");
    if (allLink) allLink.classList.add("active");
    const searchInput = document.getElementById("search-input");
    if (searchInput) searchInput.value = "";
    // Sync navbar active state
    document.querySelectorAll(".nav-links a[data-nav]").forEach(a => a.classList.remove("active"));
    const navMap = { "new": "new", "best-sellers": "best", "featured": "shop" };
    const navEl = document.querySelector(`.nav-links a[data-nav="${navMap[name] || ''}"]`);
    if (navEl) navEl.classList.add("active");
    loadProducts(1);
    _scrollToProducts();
}

function _hideTopSections() {
    const ids = ["hero-slider", "flash-banner", "shop-by-category-section", "testimonials-section"];
    ids.forEach(id => { const el = document.getElementById(id); if (el) el.style.display = "none"; });
    document.querySelectorAll(".featured-section").forEach(s => s.style.display = "none");
}

function _restoreTopSections() {
    const map = {
        "hero-slider": "",
        "flash-banner": "",
        "shop-by-category-section": "",
        "testimonials-section": "",
    };
    Object.keys(map).forEach(id => { const el = document.getElementById(id); if (el) el.style.display = ""; });
    document.querySelectorAll(".featured-section").forEach(s => s.style.display = "");
    // Reset navbar active state to "Shop All"
    document.querySelectorAll(".nav-links a[data-nav]").forEach(a => a.classList.remove("active"));
    const shopLink = document.querySelector('.nav-links a[data-nav="shop"]');
    if (shopLink) shopLink.classList.add("active");
}

function applySortAndRender() {
    renderProductCards(currentProducts);
}

function renderProductCards(items) {
    const container = document.getElementById("products-grid");
    if (!items || items.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">\uD83D\uDD0D</div><h3>No products found</h3><p>Try a different search or category</p></div>';
        return;
    }
    container.innerHTML = items.map((p, i) => renderProductCard(p, i)).join("");
}

function renderProducts(data) {
    currentProducts = data.items || [];
    const countEl = document.getElementById("product-count");
    if (countEl) countEl.textContent = `${data.total || currentProducts.length} product${(data.total || currentProducts.length) !== 1 ? "s" : ""}`;
    applySortAndRender();
    renderPagination(data);
}

function renderPagination(data) {
    const container = document.getElementById("pagination");
    if (!container || data.pages <= 1) {
        if (container) container.innerHTML = "";
        return;
    }
    let html = "";
    for (let i = 1; i <= data.pages; i++) {
        html += `<a href="#" class="page-link ${i === data.page ? "active" : ""}" onclick="loadProducts(${i}); return false;">${i}</a>`;
    }
    container.innerHTML = html;
}

async function loadCategories() {
    const container = document.getElementById("category-filter");
    if (!container) return;

    try {
        const categories = await api.get("/api/products/categories");
        let html = '<a href="#" class="category-link active" onclick="filterByCategory(null, this); return false;">All Categories</a>';
        categories.forEach(cat => {
            html += `<a href="#" class="category-link" data-name="${cat.name}" onclick="filterByCategory(${cat.id}, this); return false;">${getCategoryIcon(cat.name)} ${cat.name}</a>`;
        });
        container.innerHTML = html;
    } catch (e) {
        container.innerHTML = "";
    }
}

function _scrollToProducts() {
    const section = document.getElementById("products");
    if (!section) return;
    const headerH = (document.querySelector(".navbar")?.offsetHeight) || 0;
    const top = section.getBoundingClientRect().top + window.pageYOffset - headerH - 8;
    window.scrollTo({ top, behavior: "smooth" });
}

function filterByCategory(categoryId, el) {
    document.querySelectorAll(".category-link").forEach(a => a.classList.remove("active"));
    if (el) {
        el.classList.add("active");
    } else {
        // Caller didn't pass the clicked element (e.g., shop-by-category card on
        // the storefront). Sync the sidebar highlight by category id.
        const target = categoryId
            ? document.querySelector(`.category-link[onclick*="filterByCategory(${categoryId},"]`)
            : document.querySelector('.category-link[onclick*="filterByCategory(null"]');
        if (target) target.classList.add("active");
    }
    currentCategory = categoryId;
    currentSearch = null;
    if (categoryId !== CLOTHING_CATEGORY_ID) currentGender = null;
    const searchInput = document.getElementById("search-input");
    if (searchInput) searchInput.value = "";
    loadProducts(1, categoryId, null);
    _scrollToProducts();
}

function handleSearch(e) {
    e.preventDefault();
    const query = document.getElementById("search-input").value.trim();
    currentCategory = null;
    document.querySelectorAll(".category-link").forEach(a => a.classList.remove("active"));
    const allLink = document.querySelector(".category-link");
    if (allLink) allLink.classList.add("active");
    loadProducts(1, null, query || null);
}

function handleSort(value) {
    currentSort = value;
    loadProducts(1);
}

function applyPriceFilter() {
    const minEl = document.getElementById("price-min");
    const maxEl = document.getElementById("price-max");
    currentMinPrice = minEl && minEl.value ? parseFloat(minEl.value) : null;
    currentMaxPrice = maxEl && maxEl.value ? parseFloat(maxEl.value) : null;
    loadProducts(1);
}

function clearPriceFilter() {
    currentMinPrice = null;
    currentMaxPrice = null;
    const minEl = document.getElementById("price-min");
    const maxEl = document.getElementById("price-max");
    if (minEl) minEl.value = "";
    if (maxEl) maxEl.value = "";
    loadProducts(1);
}

async function loadPriceRange() {
    try {
        const range = await api.get("/api/products/price-range");
        const minEl = document.getElementById("price-min");
        const maxEl = document.getElementById("price-max");
        if (minEl) minEl.placeholder = `$${Math.floor(range.min)}`;
        if (maxEl) maxEl.placeholder = `$${Math.ceil(range.max)}`;
    } catch (e) { /* ignore */ }
}

function clearSearch() {
    currentSearch = null;
    const searchInput = document.getElementById("search-input");
    if (searchInput) searchInput.value = "";
    loadProducts(1, currentCategory, null);
}

function clearCategoryFilter() {
    currentCategory = null;
    document.querySelectorAll(".category-link").forEach(a => a.classList.remove("active"));
    const allLink = document.querySelector(".category-link");
    if (allLink) allLink.classList.add("active");
    loadProducts(1, null, currentSearch);
}

function updateActiveFilters() {
    const container = document.getElementById("active-filters");
    if (!container) return;
    let html = "";
    if (currentSpecialFilter) {
        const labelMap = { "new": "New Arrivals", "best-sellers": "Best Sellers", "featured": "Featured" };
        html += `<span class="filter-pill">${labelMap[currentSpecialFilter] || currentSpecialFilter} <button onclick="clearSpecialFilter()">&times;</button></span>`;
    }
    if (currentCategory) {
        const el = document.querySelector(`.category-link[onclick*="filterByCategory(${currentCategory}"]`);
        const name = el ? el.dataset.name : "Category";
        html += `<span class="filter-pill">${name} <button onclick="clearCategoryFilter()">&times;</button></span>`;
    }
    if (currentGender) {
        html += `<span class="filter-pill">${currentGender === 'men' ? 'Men' : 'Women'} <button onclick="setGenderFilter(null)">&times;</button></span>`;
    }
    if (currentSearch) {
        html += `<span class="filter-pill">Search: "${currentSearch}" <button onclick="clearSearch()">&times;</button></span>`;
    }
    if (currentMinPrice != null || currentMaxPrice != null) {
        const label = `Price: ${currentMinPrice != null ? '$' + currentMinPrice : 'Any'} - ${currentMaxPrice != null ? '$' + currentMaxPrice : 'Any'}`;
        html += `<span class="filter-pill">${label} <button onclick="clearPriceFilter()">&times;</button></span>`;
    }
    container.innerHTML = html;
}

async function loadFeaturedProducts() {
    const container = document.getElementById("featured-grid");
    if (!container) return;
    showSkeletonCards(container, 4);
    try {
        const data = await api.get("/api/products?page=1&per_page=4");
        if (data.items && data.items.length > 0) {
            container.innerHTML = data.items.map((p, i) => renderProductCard(p, i)).join("");
        }
    } catch (e) {
        container.innerHTML = "";
    }
}

async function loadBestSellers() {
    const container = document.getElementById("best-sellers-grid");
    if (!container) return;
    showSkeletonCards(container, 4);
    try {
        const items = await api.get("/api/products/best-sellers?limit=4");
        if (items && items.length) {
            container.innerHTML = items.map((p, i) => renderProductCard(p, i)).join("");
        } else {
            const section = document.getElementById("best-sellers-section");
            if (section) section.style.display = "none";
        }
    } catch (e) {
        const section = document.getElementById("best-sellers-section");
        if (section) section.style.display = "none";
    }
}

async function loadNewArrivals() {
    const container = document.getElementById("new-arrivals-grid");
    if (!container) return;
    showSkeletonCards(container, 4);
    try {
        const items = await api.get("/api/products/new-arrivals?limit=4");
        if (items && items.length) {
            container.innerHTML = items.map((p, i) => renderProductCard(p, i)).join("");
        } else {
            const section = document.getElementById("new-arrivals-section");
            if (section) section.style.display = "none";
        }
    } catch (e) {
        const section = document.getElementById("new-arrivals-section");
        if (section) section.style.display = "none";
    }
}

async function loadHeroSlides() {
    const container = document.getElementById("hero-slider");
    if (!container) return;
    try {
        const slides = await api.get("/api/promotions?slot=hero");
        if (!slides || !slides.length) return;
        const slidesHtml = slides.map((s, i) => `
            <div class="hero-slide${i === 0 ? ' active' : ''}" style="background:linear-gradient(135deg, ${s.accent_color || '#0f172a'} 0%, #0f172a 100%);">
                <div class="hero-content">
                    <h1>${s.headline}</h1>
                    ${s.subheadline ? `<p>${s.subheadline}</p>` : ''}
                    ${s.cta_text ? `<a href="${s.cta_url || '#products'}" class="btn btn-accent btn-lg">${s.cta_text}</a>` : ''}
                </div>
            </div>`).join("");
        const dots = slides.map((_, i) => `<button class="hero-dot${i === 0 ? ' active' : ''}" onclick="setHeroSlide(${i})" aria-label="Slide ${i + 1}"></button>`).join("");
        container.innerHTML = `<div class="hero-slides">${slidesHtml}</div><div class="hero-dots">${dots}</div>`;
        if (slides.length > 1) startHeroAutoplay(slides.length);
    } catch (e) { /* hide on failure — fallback hero remains */ }
}

let _heroIndex = 0;
let _heroTimer = null;
function setHeroSlide(idx) {
    const slides = document.querySelectorAll(".hero-slide");
    const dots = document.querySelectorAll(".hero-dot");
    if (!slides.length) return;
    _heroIndex = (idx + slides.length) % slides.length;
    slides.forEach((s, i) => s.classList.toggle("active", i === _heroIndex));
    dots.forEach((d, i) => d.classList.toggle("active", i === _heroIndex));
}
function startHeroAutoplay(count) {
    if (_heroTimer) clearInterval(_heroTimer);
    _heroTimer = setInterval(() => setHeroSlide(_heroIndex + 1), 6000);
}

async function loadFlashBanner() {
    const container = document.getElementById("flash-banner");
    if (!container) return;
    try {
        const promos = await api.get("/api/promotions?slot=flash");
        if (!promos || !promos.length) return;
        const p = promos[0];
        const endsAt = p.ends_at ? new Date(p.ends_at).getTime() : null;
        container.innerHTML = `
            <div class="flash-inner" style="background:${p.accent_color || '#dc2626'};">
                <div class="flash-text">
                    <strong>${p.headline}</strong>
                    ${p.subheadline ? `<span>${p.subheadline}</span>` : ''}
                </div>
                ${endsAt ? `<div class="flash-timer" id="flash-timer" data-ends="${endsAt}"></div>` : ''}
                ${p.cta_text ? `<a href="${p.cta_url || '#products'}" class="btn btn-white btn-sm">${p.cta_text}</a>` : ''}
            </div>`;
        container.style.display = "block";
        if (endsAt) tickFlashTimer();
    } catch (e) { /* hide silently */ }
}

function tickFlashTimer() {
    const el = document.getElementById("flash-timer");
    if (!el) return;
    const ends = parseInt(el.dataset.ends, 10);
    const update = () => {
        const diff = Math.max(0, ends - Date.now());
        const h = String(Math.floor(diff / 3600000)).padStart(2, "0");
        const m = String(Math.floor((diff % 3600000) / 60000)).padStart(2, "0");
        const s = String(Math.floor((diff % 60000) / 1000)).padStart(2, "0");
        el.textContent = `Ends in ${h}:${m}:${s}`;
        if (diff === 0) {
            const banner = document.getElementById("flash-banner");
            if (banner) banner.style.display = "none";
        }
    };
    update();
    setInterval(update, 1000);
}

async function loadTestimonials() {
    const container = document.getElementById("testimonials-grid");
    if (!container) return;
    try {
        const items = await api.get("/api/testimonials?limit=3");
        if (!items || !items.length) {
            const section = document.getElementById("testimonials-section");
            if (section) section.style.display = "none";
            return;
        }
        container.innerHTML = items.map(t => `
            <div class="testimonial-card">
                <div class="testimonial-stars">${renderStars(t.rating || 5)}</div>
                <p class="testimonial-quote">&ldquo;${t.quote}&rdquo;</p>
                <div class="testimonial-author">
                    <div class="testimonial-avatar">${t.avatar_initials || (t.author_name || '?').slice(0, 1)}</div>
                    <div>
                        <strong>${t.author_name}</strong>
                        ${t.author_title ? `<span>${t.author_title}</span>` : ''}
                    </div>
                </div>
            </div>`).join("");
    } catch (e) {
        const section = document.getElementById("testimonials-section");
        if (section) section.style.display = "none";
    }
}
