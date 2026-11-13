async function api(path, options = {}) {
    const allowUnauthorized = Boolean(options.allowUnauthorized);
    const headers = { Accept: "application/json", ...(options.headers || {}) };
    const init = { method: options.method, headers, body: options.body };
    if (init.body && typeof init.body !== "string") {
        headers["Content-Type"] = "application/json";
        init.body = JSON.stringify(init.body);
    }
    const response = await fetch(path, init);
    const text = await response.text();
    let data = null;
    if (text) {
        data = JSON.parse(text);
    }
    if (response.status === 401 && !allowUnauthorized) {
        location.href = "login";
    }
    if (!response.ok) {
        const detail = data && data.detail;
        throw new Error(typeof detail === "string" ? detail : "Запрос не прошёл");
    }
    return data;
}

function esc(value) {
    return String(value).replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "\"": "&quot;",
        "'": "&#39;",
    }[ch]));
}

function showError(error, target) {
    const node = target || document.querySelector("#error");
    if (!node) {
        return;
    }
    node.hidden = false;
    node.textContent = error.message || String(error);
}

function clearError() {
    const node = document.querySelector("#error");
    if (!node) {
        return;
    }
    node.hidden = true;
    node.textContent = "";
}

document.addEventListener("click", (event) => {
    const link = event.target.closest("#logout");
    if (!link) {
        return;
    }
    event.preventDefault();
    fetch("api/logout", { method: "POST" }).finally(() => {
        location.href = "login";
    });
});
