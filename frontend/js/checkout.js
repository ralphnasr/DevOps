let cartData = null;
const MIN_ORDER_TOTAL = 20;
const PAYMENT_LABELS = { cod: "Cash on Delivery", visa: "Credit / Debit Card" };

function getSelectedPayment() {
    const el = document.querySelector('input[name="payment-method"]:checked');
    return el ? el.value : "cod";
}

function selectPayment(input) {
    document.querySelectorAll(".payment-card").forEach(c => c.classList.remove("selected"));
    const card = input.closest(".payment-card");
    if (card) card.classList.add("selected");
}

function getSavedAddresses() {
    try { return JSON.parse(localStorage.getItem("shopcloud_addresses") || "[]"); }
    catch (e) { return []; }
}

function renderSavedAddressPicker() {
    const picker = document.getElementById("saved-addresses-picker");
    if (!picker) return;
    const addresses = getSavedAddresses();
    if (addresses.length === 0) {
        picker.style.display = "none";
        return;
    }
    picker.style.display = "block";
    picker.innerHTML = `
        <h4 class="picker-heading">Use a saved address</h4>
        <div class="picker-grid">
            ${addresses.map((a, i) => `
                <button type="button" class="picker-card ${a.isDefault ? 'is-default' : ''}" data-idx="${i}" onclick="selectSavedAddress(${i})">
                    ${a.isDefault ? '<span class="picker-badge">Default</span>' : ''}
                    <strong>${a.name}</strong>
                    <span>${a.address}</span>
                    <span>${a.city}${a.state ? ', ' + a.state : ''} ${a.zip || ''}</span>
                    <span>${a.country}</span>
                </button>
            `).join("")}
            <button type="button" class="picker-card picker-card-new" onclick="selectSavedAddress(-1)">
                <span class="picker-plus">&plus;</span>
                <strong>Use a new address</strong>
            </button>
        </div>
        <p class="picker-hint">Manage saved addresses in <a href="account.html">My Account</a>.</p>`;

    // Auto-select default if any
    const defaultIdx = addresses.findIndex(a => a.isDefault);
    if (defaultIdx >= 0) selectSavedAddress(defaultIdx);
}

function selectSavedAddress(index) {
    document.querySelectorAll("#saved-addresses-picker .picker-card").forEach(c => c.classList.remove("selected"));
    if (index === -1) {
        const newCard = document.querySelector("#saved-addresses-picker .picker-card-new");
        if (newCard) newCard.classList.add("selected");
        // Clear form except email (which is from auth)
        ["ship-name", "ship-address", "ship-city", "ship-state", "ship-zip"].forEach(id => {
            const el = document.getElementById(id); if (el) el.value = "";
        });
        const country = document.getElementById("ship-country");
        if (country) country.value = "Lebanon";
        return;
    }
    const a = getSavedAddresses()[index];
    if (!a) return;
    const card = document.querySelector(`#saved-addresses-picker .picker-card[data-idx="${index}"]`);
    if (card) card.classList.add("selected");
    document.getElementById("ship-name").value = a.name || "";
    document.getElementById("ship-address").value = a.address || "";
    document.getElementById("ship-city").value = a.city || "";
    document.getElementById("ship-state").value = a.state || "";
    document.getElementById("ship-zip").value = a.zip || "";
    const country = document.getElementById("ship-country");
    if (country && a.country) country.value = a.country;
}

async function loadCheckoutSummary() {
    const summaryEl = document.getElementById("checkout-summary");
    const shippingEl = document.getElementById("shipping-form");

    // Show shipping form first (Step 2)
    if (shippingEl) {
        shippingEl.style.display = "block";
        if (summaryEl) summaryEl.style.display = "none";
        const email = getUserEmail();
        if (email) {
            const emailInput = document.getElementById("ship-email");
            if (emailInput) emailInput.value = email;
        }
        renderSavedAddressPicker();
    }

    // Pre-load cart data in background
    try {
        cartData = await api.get("/api/cart");
        if (!cartData.items || cartData.items.length === 0) {
            if (shippingEl) shippingEl.style.display = "none";
            if (summaryEl) {
                summaryEl.style.display = "block";
                summaryEl.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128722;</div>
                        <h3>Your cart is empty</h3>
                        <p>Add some products before checking out.</p>
                        <a href="index.html" class="btn btn-primary">Browse Products</a>
                    </div>`;
            }
            document.querySelector(".checkout-steps").style.display = "none";
        }
    } catch (e) {
        if (shippingEl) shippingEl.style.display = "none";
        if (summaryEl) {
            summaryEl.style.display = "block";
            showError(summaryEl, "Failed to load cart. Please try again.");
        }
    }
}

function proceedToConfirm() {
    const name = document.getElementById("ship-name").value.trim();
    const email = document.getElementById("ship-email").value.trim();
    const address = document.getElementById("ship-address").value.trim();
    const city = document.getElementById("ship-city").value.trim();

    if (!name || !email || !address || !city) {
        showToast("Please fill in all required fields", "error");
        return;
    }

    if (cartData && cartData.items && cartData.items.length > 0) {
        const subtotal = cartData.items.reduce((s, i) => s + i.price * i.quantity, 0);
        if (subtotal < MIN_ORDER_TOTAL) {
            showToast(`Minimum order is $${MIN_ORDER_TOTAL.toFixed(2)}. Add $${(MIN_ORDER_TOTAL - subtotal).toFixed(2)} more to checkout.`, "error");
            return;
        }
    }

    // Persist if "save this address" is checked and not a duplicate of an existing one
    const saveToggle = document.getElementById("ship-save");
    if (saveToggle && saveToggle.checked) {
        const state = document.getElementById("ship-state").value.trim();
        const zip = document.getElementById("ship-zip").value.trim();
        const country = document.getElementById("ship-country").value;
        const list = getSavedAddresses();
        const dup = list.find(a =>
            a.name === name && a.address === address && a.city === city &&
            (a.state || "") === state && (a.zip || "") === zip);
        if (!dup) {
            list.push({ name, address, city, state, zip, country, isDefault: list.length === 0 });
            localStorage.setItem("shopcloud_addresses", JSON.stringify(list));
            showToast("Address saved to your account", "success");
        }
        saveToggle.checked = false;
    }

    // Update step UI
    updateStepUI(3);

    // Hide shipping, show summary
    document.getElementById("shipping-form").style.display = "none";
    const summaryEl = document.getElementById("checkout-summary");
    summaryEl.style.display = "block";

    if (!cartData || !cartData.items || cartData.items.length === 0) {
        showError(summaryEl, "Cart is empty.");
        return;
    }

    let subtotal = 0;
    const rows = cartData.items.map(item => {
        const lineSubtotal = item.price * item.quantity;
        subtotal += lineSubtotal;
        return `<tr><td>${item.name}</td><td>${item.quantity}</td><td>$${lineSubtotal.toFixed(2)}</td></tr>`;
    }).join("");

    const applied = (typeof getAppliedCoupon === "function") ? getAppliedCoupon() : null;
    const discount = applied ? applied.discount_amount : 0;
    const total = Math.max(0, subtotal - discount);
    const tfoot = applied
        ? `<tr><th colspan="2">Subtotal</th><th>$${subtotal.toFixed(2)}</th></tr>
           <tr><th colspan="2" style="color:var(--success);">Discount (${applied.code})</th><th style="color:var(--success);">&minus;$${discount.toFixed(2)}</th></tr>
           <tr><th colspan="2">Total</th><th>$${total.toFixed(2)}</th></tr>`
        : `<tr><th colspan="2">Total</th><th>$${total.toFixed(2)}</th></tr>`;

    summaryEl.innerHTML = `
        <h3 style="margin-bottom:20px;color:var(--navy);">Order Review</h3>
        <table class="checkout-table">
            <thead><tr><th>Product</th><th>Qty</th><th>Subtotal</th></tr></thead>
            <tbody>${rows}</tbody>
            <tfoot>${tfoot}</tfoot>
        </table>
        <div style="background:var(--bg-light);padding:16px;border-radius:8px;margin-bottom:20px;font-size:14px;color:var(--text-light);display:grid;gap:6px;">
            <div><strong>Shipping to:</strong> ${name}, ${address}, ${city}, ${document.getElementById("ship-country").value}</div>
            <div><strong>Payment:</strong> ${PAYMENT_LABELS[getSelectedPayment()] || "Cash on Delivery"}</div>
        </div>
        <div class="checkout-actions">
            <button class="btn btn-outline" onclick="backToShipping()">Back to Shipping</button>
            <button onclick="submitCheckout()" class="btn btn-primary btn-lg" id="checkout-btn">Confirm Order</button>
        </div>`;
}

function backToShipping() {
    updateStepUI(2);
    document.getElementById("shipping-form").style.display = "block";
    document.getElementById("checkout-summary").style.display = "none";
}

function updateStepUI(activeStep) {
    document.querySelectorAll(".step").forEach(s => {
        const step = parseInt(s.dataset.step);
        s.classList.toggle("active", step === activeStep);
        s.classList.toggle("completed", step < activeStep);
    });
    document.querySelectorAll(".step-connector").forEach((c, i) => {
        c.classList.toggle("completed", i + 1 < activeStep);
    });
}

async function submitCheckout() {
    const btn = document.getElementById("checkout-btn");
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Processing...";
    }

    try {
        const applied = (typeof getAppliedCoupon === "function") ? getAppliedCoupon() : null;
        const body = applied ? { coupon_code: applied.code } : {};
        const paymentMethod = getSelectedPayment();
        localStorage.setItem("shopcloud_last_payment", paymentMethod);
        const result = await api.post("/api/checkout", body);
        if (typeof setAppliedCoupon === "function") setAppliedCoupon(null);
        if (typeof clearCartSizes === "function") clearCartSizes();
        showConfirmation(result, paymentMethod);
        showToast("Order placed successfully!", "success");
    } catch (e) {
        showToast(e.message || "Checkout failed. Please try again.", "error");
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Confirm Order";
        }
    }
}

function showConfirmation(order, paymentMethod) {
    // Update steps to all completed
    document.querySelectorAll(".step").forEach(s => s.classList.add("completed"));
    document.querySelectorAll(".step").forEach(s => s.classList.remove("active"));
    document.querySelectorAll(".step-connector").forEach(c => c.classList.add("completed"));

    const container = document.getElementById("checkout-summary");
    const breakdown = (order.discount_amount && order.discount_amount > 0) ? `
                <p><strong>Subtotal:</strong> $${(order.subtotal || 0).toFixed(2)}</p>
                <p style="color:var(--success);"><strong>Discount${order.coupon_code ? ' (' + order.coupon_code + ')' : ''}:</strong> &minus;$${order.discount_amount.toFixed(2)}</p>` : "";
    container.innerHTML = `
        <div class="order-confirmation">
            <div class="confirmation-icon">&#10003;</div>
            <h2>Order Confirmed!</h2>
            <div class="confirmation-details">
                <p><strong>Order ID:</strong> #${order.order_id}</p>
                <p><strong>Status:</strong> <span class="badge badge-confirmed">${order.status}</span></p>${breakdown}
                <p><strong>Total:</strong> $${order.total_amount.toFixed(2)}</p>
                <p><strong>Payment:</strong> ${PAYMENT_LABELS[paymentMethod] || PAYMENT_LABELS[localStorage.getItem("shopcloud_last_payment")] || "Cash on Delivery"}</p>
            </div>
            <p>${order.message}</p>
            <div class="confirmation-actions">
                <a href="orders.html" class="btn btn-primary">View My Orders</a>
                <a href="index.html" class="btn btn-outline">Continue Shopping</a>
            </div>
        </div>`;
}
