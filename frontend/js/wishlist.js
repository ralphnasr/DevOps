/* Wishlist */

function getWishlist() {
    try { return JSON.parse(localStorage.getItem("shopcloud_wishlist") || "[]"); }
    catch (e) { return []; }
}

function saveWishlist(list) {
    localStorage.setItem("shopcloud_wishlist", JSON.stringify(list));
    updateWishlistBadge();
}

function isInWishlist(productId) {
    return getWishlist().includes(Number(productId));
}

function toggleWishlist(productId, event) {
    if (event) event.stopPropagation();
    const id = Number(productId);
    let list = getWishlist();
    if (list.includes(id)) {
        list = list.filter(x => x !== id);
        showToast("Removed from wishlist", "info");
    } else {
        list.push(id);
        showToast("Added to wishlist", "success");
    }
    saveWishlist(list);
    const isActive = list.includes(id);
    // Update small heart buttons (product cards)
    document.querySelectorAll(`.wishlist-btn[data-wishlist-id="${id}"]`).forEach(btn => {
        btn.classList.toggle("active", isActive);
        btn.innerHTML = isActive ? "&#9829;" : "&#9825;";
    });
    // Update prominent PDP buttons (icon + label)
    refreshPdpWishlistButtons(id, isActive);
}

/* Silent removal — no toast, no event. Called from addToCart auto-remove. */
function removeFromWishlist(productId) {
    const id = Number(productId);
    let list = getWishlist();
    if (!list.includes(id)) return false;
    list = list.filter(x => x !== id);
    saveWishlist(list);
    document.querySelectorAll(`.wishlist-btn[data-wishlist-id="${id}"]`).forEach(btn => {
        btn.classList.remove("active");
        btn.innerHTML = "&#9825;";
    });
    refreshPdpWishlistButtons(id, false);
    return true;
}

function updateWishlistBadge() {
    const badge = document.getElementById("wishlist-badge");
    if (!badge) return;
    const count = getWishlist().length;
    badge.textContent = count;
    badge.style.display = count > 0 ? "inline" : "none";
}

function wishlistButtonHtml(productId) {
    const active = isInWishlist(productId);
    return `<button class="wishlist-btn ${active ? 'active' : ''}" data-wishlist-id="${productId}" onclick="toggleWishlist(${productId}, event)" title="${active ? 'Remove from' : 'Add to'} wishlist">${active ? '&#9829;' : '&#9825;'}</button>`;
}

/* Larger "Save to Wishlist" toggle for the PDP — full-width, with label */
function wishlistPdpButtonHtml(productId) {
    const active = isInWishlist(productId);
    return `<button class="wishlist-pdp-btn ${active ? 'active' : ''}" data-wishlist-id="${productId}" onclick="toggleWishlist(${productId}, event)" type="button">
        <span class="wishlist-pdp-icon">${active ? '&#9829;' : '&#9825;'}</span>
        <span class="wishlist-pdp-label">${active ? 'Saved to Wishlist' : 'Save to Wishlist'}</span>
    </button>`;
}

/* Refresh the PDP heart label after toggle (called from toggleWishlist) */
function refreshPdpWishlistButtons(productId, isActive) {
    document.querySelectorAll(`.wishlist-pdp-btn[data-wishlist-id="${productId}"]`).forEach(btn => {
        btn.classList.toggle("active", isActive);
        const icon = btn.querySelector(".wishlist-pdp-icon");
        const label = btn.querySelector(".wishlist-pdp-label");
        if (icon) icon.innerHTML = isActive ? "&#9829;" : "&#9825;";
        if (label) label.textContent = isActive ? "Saved to Wishlist" : "Save to Wishlist";
    });
}

async function loadWishlistPage() {
    const container = document.getElementById("wishlist-container");
    if (!container) return;

    const list = getWishlist();
    if (list.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">&#9825;</div>
                <h3>Your wishlist is empty</h3>
                <p>Save products you love for later</p>
                <a href="index.html" class="btn btn-primary">Browse Products</a>
            </div>`;
        return;
    }

    showSkeletonCards(container, list.length);

    try {
        const data = await api.get("/api/products?per_page=100");
        const products = (data.items || []).filter(p => list.includes(p.id));
        const missing = list.filter(id => !products.find(p => p.id === id));
        // Clean up removed products
        if (missing.length > 0) {
            saveWishlist(list.filter(id => !missing.includes(id)));
        }

        if (products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">&#9825;</div>
                    <h3>Your wishlist is empty</h3>
                    <p>Products you saved may no longer be available</p>
                    <a href="index.html" class="btn btn-primary">Browse Products</a>
                </div>`;
            return;
        }

        container.innerHTML = `
            <div class="wishlist-count">${products.length} item${products.length !== 1 ? 's' : ''} saved</div>
            <div class="wishlist-list">
                ${products.map((p, i) => renderWishlistRow(p, i)).join("")}
            </div>`;
    } catch (e) {
        showError(container, "Failed to load wishlist products.");
    }
}

/* Compact rectangular wishlist row (replaces big square product cards) */
function renderWishlistRow(product, index) {
    const delay = (index || 0) * 0.05;
    const catName = product.category ? product.category.name : "";
    const inStock = (product.stock_quantity || 0) > 0;
    return `
    <div class="wishlist-row fade-in-up" style="animation-delay:${delay}s">
        <a class="wishlist-row-thumb" href="product.html?id=${product.id}">
            ${productImageHtml(product, 110)}
        </a>
        <div class="wishlist-row-info">
            <p class="wishlist-row-cat">${catName}</p>
            <a class="wishlist-row-name" href="product.html?id=${product.id}">${product.name}</a>
            <p class="wishlist-row-stock ${inStock ? '' : 'oos'}">${inStock ? (product.stock_quantity < 10 ? 'Low stock — ' + product.stock_quantity + ' left' : 'In stock') : 'Out of stock'}</p>
        </div>
        <div class="wishlist-row-price">$${product.price.toFixed(2)}</div>
        <div class="wishlist-row-actions">
            <button class="btn btn-accent btn-sm" ${inStock ? '' : 'disabled'} onclick="addToCart(${product.id})">Add to Cart</button>
            <button class="wishlist-row-remove" onclick="toggleWishlist(${product.id}); setTimeout(loadWishlistPage, 250);" aria-label="Remove from wishlist">&times;</button>
        </div>
    </div>`;
}

/* Recently viewed */
function trackRecentlyViewed(productId) {
    const id = Number(productId);
    let viewed = getRecentlyViewed();
    viewed = viewed.filter(x => x !== id);
    viewed.unshift(id);
    if (viewed.length > 12) viewed = viewed.slice(0, 12);
    localStorage.setItem("shopcloud_recently_viewed", JSON.stringify(viewed));
}

function getRecentlyViewed() {
    try { return JSON.parse(localStorage.getItem("shopcloud_recently_viewed") || "[]"); }
    catch (e) { return []; }
}

async function loadRecentlyViewed(containerId, excludeId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const viewed = getRecentlyViewed().filter(id => id !== Number(excludeId));
    if (viewed.length === 0) return;

    try {
        const data = await api.get("/api/products?per_page=100");
        const products = viewed.slice(0, 4).map(id => (data.items || []).find(p => p.id === id)).filter(Boolean);
        if (products.length === 0) return;

        container.closest("section").style.display = "block";
        container.innerHTML = products.map((p, i) => renderProductCard(p, i)).join("");
    } catch (e) {}
}
