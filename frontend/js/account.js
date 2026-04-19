/* Account — profile, security, preferences, addresses */

function loadAccountPage() {
    loadProfile();
    loadSecuritySettings();
    loadEmailPreferences();
    loadAddresses();
}

function loadProfile() {
    const { idToken } = getTokens();
    const payload = parseJwt(idToken);
    const email = payload ? payload.email : "Unknown";
    const sub = payload ? payload.sub : "Unknown";
    const exp = payload && payload.exp ? new Date(payload.exp * 1000).toLocaleDateString() : "N/A";

    document.getElementById("profile-email").textContent = email;
    document.getElementById("profile-id").textContent = sub;
    document.getElementById("profile-provider").textContent = isDevMode() ? "Local" : "OAuth";
    document.getElementById("profile-session-exp").textContent = exp;

    const initial = email ? email.charAt(0).toUpperCase() : "?";
    document.getElementById("profile-avatar").textContent = initial;
}

function loadSecuritySettings() {
    const mfaEnabled = localStorage.getItem("shopcloud_mfa_enabled") === "true";
    document.getElementById("mfa-toggle").checked = mfaEnabled;
    document.getElementById("mfa-status").textContent = mfaEnabled ? "Enabled" : "Disabled";
    document.getElementById("mfa-status").className = "setting-status " + (mfaEnabled ? "status-on" : "status-off");
}

function changePassword() {
    const current = document.getElementById("current-password").value;
    const newPw = document.getElementById("new-password").value;
    const confirm = document.getElementById("confirm-password").value;

    if (!current || !newPw || !confirm) {
        showToast("Please fill in all password fields", "error");
        return;
    }
    if (newPw.length < 8) {
        showToast("Password must be at least 8 characters", "error");
        return;
    }
    if (newPw !== confirm) {
        showToast("New passwords do not match", "error");
        return;
    }
    if (!/[A-Z]/.test(newPw) || !/[a-z]/.test(newPw) || !/[0-9]/.test(newPw)) {
        showToast("Password must include uppercase, lowercase, and numbers", "error");
        return;
    }

    showToast("Password updated", "success");

    document.getElementById("current-password").value = "";
    document.getElementById("new-password").value = "";
    document.getElementById("confirm-password").value = "";
}

function toggleMFA() {
    const enabled = document.getElementById("mfa-toggle").checked;
    localStorage.setItem("shopcloud_mfa_enabled", enabled);
    document.getElementById("mfa-status").textContent = enabled ? "Enabled" : "Disabled";
    document.getElementById("mfa-status").className = "setting-status " + (enabled ? "status-on" : "status-off");
    showToast(enabled ? "Two-factor authentication enabled" : "Two-factor authentication disabled", "success");
}

function getEmailPreferences() {
    try {
        return JSON.parse(localStorage.getItem("shopcloud_email_prefs") || '{}');
    } catch (e) { return {}; }
}

function loadEmailPreferences() {
    const prefs = getEmailPreferences();
    document.getElementById("pref-order-confirm").checked = prefs.orderConfirmation !== false;
    document.getElementById("pref-order-shipped").checked = prefs.orderShipped !== false;
    document.getElementById("pref-order-delivered").checked = prefs.orderDelivered !== false;
    document.getElementById("pref-newsletter").checked = prefs.newsletter === true;
    document.getElementById("pref-promotions").checked = prefs.promotions === true;
    document.getElementById("pref-restock").checked = prefs.restock === true;
}

function saveEmailPreferences() {
    const prefs = {
        orderConfirmation: document.getElementById("pref-order-confirm").checked,
        orderShipped: document.getElementById("pref-order-shipped").checked,
        orderDelivered: document.getElementById("pref-order-delivered").checked,
        newsletter: document.getElementById("pref-newsletter").checked,
        promotions: document.getElementById("pref-promotions").checked,
        restock: document.getElementById("pref-restock").checked,
    };
    localStorage.setItem("shopcloud_email_prefs", JSON.stringify(prefs));
    showToast("Email preferences saved", "success");
}

function getAddresses() {
    try { return JSON.parse(localStorage.getItem("shopcloud_addresses") || "[]"); }
    catch (e) { return []; }
}

function loadAddresses() {
    const container = document.getElementById("addresses-list");
    if (!container) return;
    const addresses = getAddresses();
    if (addresses.length === 0) {
        container.innerHTML = '<p class="text-muted">No saved addresses. Add one during checkout or below.</p>';
        return;
    }
    container.innerHTML = addresses.map((addr, i) => `
        <div class="address-card ${addr.isDefault ? 'default' : ''}">
            ${addr.isDefault ? '<span class="badge badge-confirmed">Default</span>' : ''}
            <strong>${addr.name}</strong>
            <p>${addr.address}, ${addr.city}${addr.state ? ', ' + addr.state : ''} ${addr.zip || ''}</p>
            <p>${addr.country}</p>
            <div class="address-actions">
                ${!addr.isDefault ? `<button class="btn btn-outline btn-sm" onclick="setDefaultAddress(${i})">Set Default</button>` : ''}
                <button class="btn btn-outline btn-sm" onclick="showAddressForm(${i})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteAddress(${i})">Delete</button>
            </div>
        </div>
    `).join("");
}

let _editingAddressIndex = null;

function showAddressForm(index) {
    _editingAddressIndex = (typeof index === "number") ? index : null;
    const heading = document.getElementById("address-form-heading");
    const submitBtn = document.getElementById("address-form-submit");
    if (_editingAddressIndex !== null) {
        const a = getAddresses()[_editingAddressIndex];
        if (a) {
            document.getElementById("addr-name").value = a.name || "";
            document.getElementById("addr-address").value = a.address || "";
            document.getElementById("addr-city").value = a.city || "";
            document.getElementById("addr-state").value = a.state || "";
            document.getElementById("addr-zip").value = a.zip || "";
            document.getElementById("addr-country").value = a.country || "Lebanon";
        }
        if (heading) heading.textContent = "Edit Address";
        if (submitBtn) submitBtn.textContent = "Save Changes";
    } else {
        clearAddressForm();
        if (heading) heading.textContent = "Add Address";
        if (submitBtn) submitBtn.textContent = "Save Address";
    }
    document.getElementById("address-form-modal").style.display = "block";
}

function hideAddressForm() {
    document.getElementById("address-form-modal").style.display = "none";
    _editingAddressIndex = null;
}

function clearAddressForm() {
    ["addr-name", "addr-address", "addr-city", "addr-state", "addr-zip"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = "";
    });
    const country = document.getElementById("addr-country");
    if (country) country.value = "Lebanon";
}

function saveNewAddress() {
    const name = document.getElementById("addr-name").value.trim();
    const address = document.getElementById("addr-address").value.trim();
    const city = document.getElementById("addr-city").value.trim();
    const state = document.getElementById("addr-state").value.trim();
    const zip = document.getElementById("addr-zip").value.trim();
    const country = document.getElementById("addr-country").value;

    if (!name || !address || !city) {
        showToast("Please fill in name, address, and city", "error");
        return;
    }

    const addresses = getAddresses();
    if (_editingAddressIndex !== null && addresses[_editingAddressIndex]) {
        const existing = addresses[_editingAddressIndex];
        addresses[_editingAddressIndex] = { ...existing, name, address, city, state, zip, country };
        showToast("Address updated", "success");
    } else {
        addresses.push({ name, address, city, state, zip, country, isDefault: addresses.length === 0 });
        showToast("Address saved", "success");
    }
    localStorage.setItem("shopcloud_addresses", JSON.stringify(addresses));
    hideAddressForm();
    clearAddressForm();
    loadAddresses();
}

function setDefaultAddress(index) {
    const addresses = getAddresses();
    addresses.forEach((a, i) => { a.isDefault = i === index; });
    localStorage.setItem("shopcloud_addresses", JSON.stringify(addresses));
    loadAddresses();
    showToast("Default address updated", "success");
}

function deleteAddress(index) {
    const addresses = getAddresses();
    const wasDefault = addresses[index].isDefault;
    addresses.splice(index, 1);
    if (wasDefault && addresses.length > 0) addresses[0].isDefault = true;
    localStorage.setItem("shopcloud_addresses", JSON.stringify(addresses));
    loadAddresses();
    showToast("Address removed", "info");
}

function deleteAccount() {
    if (!confirm("Are you sure you want to delete your account? This action cannot be undone.")) return;
    localStorage.removeItem("shopcloud_wishlist");
    localStorage.removeItem("shopcloud_recently_viewed");
    localStorage.removeItem("shopcloud_email_prefs");
    localStorage.removeItem("shopcloud_addresses");
    localStorage.removeItem("shopcloud_mfa_enabled");
    clearTokens();
    showToast("Account deleted", "info");
    setTimeout(() => { window.location.href = "index.html"; }, 1500);
}
