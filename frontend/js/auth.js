function _assertLocalhost() {
    // Guard: dev-mode token minting is only permitted when served from localhost.
    // If deploy-frontend.sh's config.js rewrite ever fails, this prevents the
    // deployed site from accepting fake JWTs.
    const host = window.location.hostname;
    if (host !== "localhost" && host !== "127.0.0.1") {
        const msg = "Dev login disabled: this site is deployed but Cognito is not configured. Contact the administrator.";
        showToast && showToast(msg, "error");
        throw new Error(msg);
    }
}

function devLogin(email, password) {
    _assertLocalhost();
    const header = btoa(JSON.stringify({ alg: "none", typ: "JWT" }));
    const payload = btoa(JSON.stringify({
        sub: "local-user",
        email: email || "user@local",
        name: email ? email.split("@")[0] : "Dev User",
        exp: Math.floor(Date.now() / 1000) + 86400,
    }));
    const fakeToken = `${header}.${payload}.dev`;
    setTokens(fakeToken, null);

    // Save email if "Remember me" is checked
    const rememberMe = document.getElementById("remember-me");
    if (rememberMe && rememberMe.checked) {
        localStorage.setItem("shopcloud_email", email);
    } else {
        localStorage.removeItem("shopcloud_email");
    }

    showToast && showToast("Welcome back!", "success");
    setTimeout(() => { window.location.href = "index.html"; }, 500);
}

function devRegister(name, email, password) {
    _assertLocalhost();
    const header = btoa(JSON.stringify({ alg: "none", typ: "JWT" }));
    const payload = btoa(JSON.stringify({
        sub: "local-user-" + Date.now(),
        email: email,
        name: name,
        exp: Math.floor(Date.now() / 1000) + 86400,
    }));
    const fakeToken = `${header}.${payload}.dev`;
    setTokens(fakeToken, null);

    localStorage.setItem("shopcloud_email", email);
    showToast && showToast("Account created! Welcome to ShopCloud.", "success");
    setTimeout(() => { window.location.href = "index.html"; }, 800);
}

function isDevMode() {
    const host = window.location.hostname;
    const isLocal = host === "localhost" || host === "127.0.0.1";
    return isLocal && !CONFIG.COGNITO_DOMAIN;
}

/* OAuth helpers (kept for social/external IdP flows) */
function getLoginUrl() {
    const params = new URLSearchParams({
        response_type: "code",
        client_id: CONFIG.COGNITO_CLIENT_ID,
        redirect_uri: CONFIG.COGNITO_REDIRECT_URI,
        scope: CONFIG.COGNITO_SCOPES,
    });
    return `${CONFIG.COGNITO_DOMAIN}/login?${params.toString()}`;
}

function redirectToLogin() {
    // Always go to our in-page login form. Prod no longer uses Cognito Hosted UI —
    // sign-in/up runs through cognitoSignIn() (InitiateAuth) on login.html itself,
    // so jumping to the Hosted UI mid-flow would break the single-page experience.
    window.location.href = "login.html";
}

/* ── Direct Cognito API (no Hosted UI redirect) ── */
function _cognitoEndpoint() {
    const m = (CONFIG.COGNITO_DOMAIN || "").match(/auth\.([a-z0-9-]+)\.amazoncognito\.com/);
    const region = m ? m[1] : "us-east-1";
    return `https://cognito-idp.${region}.amazonaws.com/`;
}

async function _cognitoCall(target, body) {
    const resp = await fetch(_cognitoEndpoint(), {
        method: "POST",
        headers: {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": `AWSCognitoIdentityProviderService.${target}`,
        },
        body: JSON.stringify(body),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) {
        const msg = data.message || data.__type || "Authentication error";
        const err = new Error(msg);
        err.code = data.__type || "UnknownError";
        throw err;
    }
    return data;
}

async function cognitoSignIn(email, password) {
    const data = await _cognitoCall("InitiateAuth", {
        AuthFlow: "USER_PASSWORD_AUTH",
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        AuthParameters: { USERNAME: email, PASSWORD: password },
    });
    if (!data.AuthenticationResult) {
        throw new Error(data.ChallengeName ? `Additional challenge required: ${data.ChallengeName}` : "Sign-in failed");
    }
    setTokens(data.AuthenticationResult.IdToken, data.AuthenticationResult.RefreshToken);
    return data.AuthenticationResult;
}

async function cognitoSignUp(email, password, name) {
    return await _cognitoCall("SignUp", {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
        Password: password,
        UserAttributes: [
            { Name: "email", Value: email },
            ...(name ? [{ Name: "name", Value: name }] : []),
        ],
    });
}

async function cognitoConfirmSignUp(email, code) {
    return await _cognitoCall("ConfirmSignUp", {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
        ConfirmationCode: code,
    });
}

async function cognitoResendCode(email) {
    return await _cognitoCall("ResendConfirmationCode", {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
    });
}

async function cognitoForgotPassword(email) {
    return await _cognitoCall("ForgotPassword", {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
    });
}

async function cognitoConfirmForgotPassword(email, code, newPassword) {
    return await _cognitoCall("ConfirmForgotPassword", {
        ClientId: CONFIG.COGNITO_CLIENT_ID,
        Username: email,
        ConfirmationCode: code,
        Password: newPassword,
    });
}

function _friendlyCognitoError(err) {
    const map = {
        "NotAuthorizedException": "Incorrect email or password.",
        "UserNotFoundException": "No account found with that email.",
        "UserNotConfirmedException": "Please verify your email before signing in.",
        "UsernameExistsException": "An account with that email already exists.",
        "InvalidPasswordException": "Password does not meet requirements (8+ chars, upper, lower, number).",
        "InvalidParameterException": "Please check your input and try again.",
        "CodeMismatchException": "The verification code is incorrect.",
        "ExpiredCodeException": "The verification code has expired. Request a new one.",
        "LimitExceededException": "Too many attempts. Please wait a few minutes.",
    };
    return map[err.code] || err.message || "Something went wrong. Please try again.";
}

/* ── Token storage ── */
function getTokens() {
    const idToken = sessionStorage.getItem("id_token");
    const refreshToken = sessionStorage.getItem("refresh_token");
    return { idToken, refreshToken };
}

function setTokens(idToken, refreshToken) {
    sessionStorage.setItem("id_token", idToken);
    if (refreshToken) {
        sessionStorage.setItem("refresh_token", refreshToken);
    }
}

function clearTokens() {
    sessionStorage.removeItem("id_token");
    sessionStorage.removeItem("refresh_token");
}

/* ── JWT helpers ── */
function parseJwt(token) {
    try {
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        return JSON.parse(atob(base64));
    } catch (e) {
        return null;
    }
}

function isTokenExpired(token) {
    if (!token) return true;
    const payload = parseJwt(token);
    if (!payload || !payload.exp) return true;
    return Date.now() >= payload.exp * 1000;
}

function isLoggedIn() {
    const { idToken } = getTokens();
    return idToken && !isTokenExpired(idToken);
}

function getUserEmail() {
    const { idToken } = getTokens();
    if (!idToken) return null;
    const payload = parseJwt(idToken);
    return payload ? payload.email : null;
}

function getUserName() {
    const { idToken } = getTokens();
    if (!idToken) return null;
    const payload = parseJwt(idToken);
    return payload ? (payload.name || payload.email) : null;
}

/* Token exchange */
async function exchangeCodeForTokens(code) {
    const body = new URLSearchParams({
        grant_type: "authorization_code",
        client_id: CONFIG.COGNITO_CLIENT_ID,
        code: code,
        redirect_uri: CONFIG.COGNITO_REDIRECT_URI,
    });

    const resp = await fetch(`${CONFIG.COGNITO_DOMAIN}/oauth2/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
    });

    if (!resp.ok) throw new Error("Token exchange failed");
    const data = await resp.json();
    setTokens(data.id_token, data.refresh_token);
    return data;
}

async function refreshAccessToken() {
    const { refreshToken } = getTokens();
    if (!refreshToken) return null;

    const body = new URLSearchParams({
        grant_type: "refresh_token",
        client_id: CONFIG.COGNITO_CLIENT_ID,
        refresh_token: refreshToken,
    });

    try {
        const resp = await fetch(`${CONFIG.COGNITO_DOMAIN}/oauth2/token`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: body.toString(),
        });
        if (!resp.ok) throw new Error("Refresh failed");
        const data = await resp.json();
        setTokens(data.id_token, data.refresh_token || refreshToken);
        return data.id_token;
    } catch (e) {
        clearTokens();
        return null;
    }
}

async function getValidToken() {
    const { idToken } = getTokens();
    if (idToken && !isTokenExpired(idToken)) return idToken;
    if (isDevMode()) return idToken || null;
    return await refreshAccessToken();
}

/* ── Logout ── */
function logout() {
    clearTokens();
    window.location.href = "index.html";
}

/* ── UI update ── */
function updateAuthUI() {
    const loginBtn = document.getElementById("login-btn");
    const logoutBtn = document.getElementById("logout-btn");
    const accountLink = document.getElementById("account-link");

    if (isLoggedIn()) {
        if (loginBtn) loginBtn.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "";
        if (accountLink) accountLink.style.display = "";
    } else {
        if (loginBtn) loginBtn.style.display = "";
        if (logoutBtn) logoutBtn.style.display = "none";
        if (accountLink) accountLink.style.display = "none";
    }
}
