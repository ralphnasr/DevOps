// ── Cart-item size storage (frontend-only metadata, keyed by product_id) ──
function getCartSizes() {
    try { return JSON.parse(localStorage.getItem("shopcloud_cart_sizes") || "{}"); }
    catch { return {}; }
}
function setCartSize(productId, size) {
    const m = getCartSizes();
    if (size) m[productId] = size; else delete m[productId];
    localStorage.setItem("shopcloud_cart_sizes", JSON.stringify(m));
}
function clearCartSizes() {
    localStorage.removeItem("shopcloud_cart_sizes");
}

async function loadCart() {
    const container = document.getElementById("cart-container");
    if (!container) return;
    showLoading(container);

    try {
        const cart = await api.get("/api/cart");
        renderCart(cart);
    } catch (e) {
        showError(container, "Failed to load cart. Please try again.");
    }
}

function renderCart(cart) {
    const container = document.getElementById("cart-container");

    if (!cart.items || cart.items.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">&#128722;</div>
                <h3>Your cart is empty</h3>
                <p>Looks like you haven't added anything yet.</p>
                <a href="index.html" class="btn btn-primary">Start Shopping</a>
            </div>`;
        updateCartSummary(0);
        return;
    }

    const sizes = getCartSizes();
    let total = 0;
    const rows = cart.items.map(item => {
        const subtotal = item.price * item.quantity;
        total += subtotal;
        const sizeLine = sizes[item.product_id]
            ? `<div class="cart-item-meta">Size: <strong>${sizes[item.product_id]}</strong></div>` : '';
        return `
            <tr>
                <td><div class="cart-item-thumb">&#128230;</div></td>
                <td><strong>${item.name}</strong>${sizeLine}</td>
                <td>$${item.price.toFixed(2)}</td>
                <td>
                    <div class="quantity-controls">
                        <button onclick="updateQuantity(${item.product_id}, ${item.quantity - 1})" class="btn-qty">&minus;</button>
                        <span style="min-width:24px;text-align:center;font-weight:600">${item.quantity}</span>
                        <button onclick="updateQuantity(${item.product_id}, ${item.quantity + 1})" class="btn-qty">+</button>
                    </div>
                </td>
                <td><strong>$${subtotal.toFixed(2)}</strong></td>
                <td><button onclick="removeFromCart(${item.product_id})" class="btn btn-danger btn-sm">Remove</button></td>
            </tr>`;
    }).join("");

    const applied = getAppliedCoupon();
    const discount = applied ? applied.discount_amount : 0;
    const finalTotal = Math.max(0, total - discount);

    const freeThreshold = 50;
    const remaining = Math.max(0, freeThreshold - total);
    const pct = Math.min(100, Math.round((total / freeThreshold) * 100));
    const shippingHtml = remaining > 0
        ? `<div class="free-shipping-bar">
              <p>Add <strong>$${remaining.toFixed(2)}</strong> more to qualify for <strong>FREE shipping</strong>!</p>
              <div class="progress"><div class="progress-fill" style="width:${pct}%"></div></div>
           </div>`
        : `<div class="free-shipping-bar success">
              <p>&#10003; You qualify for <strong>FREE shipping</strong>!</p>
              <div class="progress"><div class="progress-fill" style="width:100%"></div></div>
           </div>`;

    container.innerHTML = `
        ${shippingHtml}
        <table class="cart-table">
            <thead><tr><th></th><th>Product</th><th>Price</th><th>Quantity</th><th>Subtotal</th><th></th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
        <div class="cart-summary-card">
            <div class="coupon-row">
                <input type="text" id="coupon-input" placeholder="Have a promo code?" value="${applied ? applied.code : ''}" style="text-transform:uppercase;">
                ${applied
                    ? `<button onclick="removeCoupon()" class="btn btn-outline">Remove</button>`
                    : `<button onclick="applyCoupon()" class="btn btn-primary">Apply</button>`}
            </div>
            <div id="coupon-status" class="coupon-status">${applied ? `<span class="coupon-applied">&#10003; ${applied.code} applied &mdash; you save $${discount.toFixed(2)}</span>` : ''}</div>
            <div class="totals-line"><span>Subtotal</span><span>$${total.toFixed(2)}</span></div>
            ${applied ? `<div class="totals-line discount"><span>Discount (${applied.code})</span><span>&minus;$${discount.toFixed(2)}</span></div>` : ''}
            <div class="totals-line total"><span>Total</span><span>$${finalTotal.toFixed(2)}</span></div>
        </div>
        <div class="cart-actions">
            <button onclick="clearCart()" class="btn btn-outline">Clear Cart</button>
            <a href="checkout.html" class="btn btn-primary btn-lg">Proceed to Checkout</a>
        </div>`;
    updateCartSummary(finalTotal);
}

function getAppliedCoupon() {
    try {
        const raw = localStorage.getItem("applied_coupon");
        return raw ? JSON.parse(raw) : null;
    } catch { return null; }
}

function setAppliedCoupon(c) {
    if (c) localStorage.setItem("applied_coupon", JSON.stringify(c));
    else localStorage.removeItem("applied_coupon");
}

async function applyCoupon() {
    const input = document.getElementById("coupon-input");
    const code = (input.value || "").trim().toUpperCase();
    if (!code) { showToast("Enter a coupon code", "error"); return; }

    try {
        const cart = await api.get("/api/cart");
        const subtotal = cart.items.reduce((s, i) => s + i.price * i.quantity, 0);
        const result = await api.post("/api/coupons/validate", { code, cart_total: subtotal });
        if (!result.valid) {
            setAppliedCoupon(null);
            document.getElementById("coupon-status").innerHTML = `<span class="coupon-error">${result.message}</span>`;
            showToast(result.message, "error");
            return;
        }
        setAppliedCoupon({ code: result.code, discount_amount: result.discount_amount });
        showToast(`${result.code} applied — you save $${result.discount_amount.toFixed(2)}`, "success");
        loadCart();
    } catch (e) {
        showToast(e.message || "Could not apply coupon", "error");
    }
}

function removeCoupon() {
    setAppliedCoupon(null);
    showToast("Coupon removed", "info");
    loadCart();
}

function updateCartSummary(total) {
    const el = document.getElementById("cart-total");
    if (el) el.textContent = `$${total.toFixed(2)}`;
}

async function addToCart(productId, quantity, size) {
    if (quantity === undefined) quantity = 1;
    if (!isLoggedIn()) {
        showToast("Please log in to add items to cart", "error");
        setTimeout(() => redirectToLogin(), 1500);
        return;
    }
    try {
        await api.post("/api/cart/items", { product_id: productId, quantity });
        if (size) setCartSize(productId, size);
        updateCartBadge();
        const removed = (typeof removeFromWishlist === "function") && removeFromWishlist(productId);
        showToast(removed ? "Added to cart &mdash; removed from wishlist" : "Added to cart!", "success");
        // If we're on the wishlist page, re-render so the item disappears
        if (removed && typeof loadWishlistPage === "function" && document.getElementById("wishlist-container")) {
            setTimeout(loadWishlistPage, 250);
        }
    } catch (e) {
        showToast(e.message || "Failed to add to cart", "error");
    }
}

async function updateQuantity(productId, quantity) {
    try {
        if (quantity <= 0) {
            await api.delete(`/api/cart/items/${productId}`);
        } else {
            await api.put(`/api/cart/items/${productId}`, { quantity });
        }
        loadCart();
        updateCartBadge();
    } catch (e) {
        showToast(e.message || "Failed to update quantity", "error");
    }
}

async function removeFromCart(productId) {
    try {
        await api.delete(`/api/cart/items/${productId}`);
        setCartSize(productId, null);
        loadCart();
        updateCartBadge();
        showToast("Item removed", "info");
    } catch (e) {
        showToast(e.message || "Failed to remove item", "error");
    }
}

async function clearCart() {
    if (!confirm("Clear all items from your cart?")) return;
    try {
        await api.delete("/api/cart");
        clearCartSizes();
        loadCart();
        updateCartBadge();
        showToast("Cart cleared", "info");
    } catch (e) {
        showToast(e.message || "Failed to clear cart", "error");
    }
}
