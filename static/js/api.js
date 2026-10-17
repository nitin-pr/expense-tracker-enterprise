/**
 * Shared authenticated-fetch helper for every page beyond login/signup.
 * Centralizes: attaching the Bearer token, redirecting to /login/ if it's
 * missing or the backend rejects it (expired - Firebase ID tokens last an
 * hour), and building JSON request bodies consistently.
 */

export function requireToken() {
    const token = sessionStorage.getItem("idToken");
    if (!token) {
        window.location.href = "/login/";
        return null;
    }
    return token;
}

export async function apiFetch(path, options = {}) {
    const token = requireToken();
    if (!token) return null;

    const headers = { Authorization: `Bearer ${token}`, ...(options.headers || {}) };
    if (options.body !== undefined && !(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
    }

    const response = await fetch(path, { ...options, headers });

    if (response.status === 401) {
        sessionStorage.removeItem("idToken");
        window.location.href = "/login/";
        return null;
    }
    return response;
}

export async function apiGet(path) {
    const response = await apiFetch(path);
    return response ? response.json() : null;
}

export async function apiJson(path, method, data) {
    const response = await apiFetch(path, { method, body: JSON.stringify(data) });
    if (!response) return { ok: false, data: null };
    const body = response.status === 204 ? null : await response.json();
    return { ok: response.ok, status: response.status, data: body };
}

export function logout() {
    sessionStorage.removeItem("idToken");
    window.location.href = "/login/";
}
