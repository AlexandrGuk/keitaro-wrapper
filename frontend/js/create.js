let prefix = "test_guk_";
let picked = null;

const nameInput = document.querySelector("#name");
const geoInput = document.querySelector("#geo");
const offerInput = document.querySelector("#offer");
const offerList = document.querySelector("#offer-list");
const finalName = document.querySelector("#final-name");
const form = document.querySelector("#create-form");

function campaignName(raw) {
    let tail = raw.trim().toLowerCase().replace(/ /g, "_");
    tail = tail.replace(/[^a-z0-9_]+/g, "_").replace(/_+/g, "_").replace(/^_|_$/g, "");
    if (!tail) {
        return prefix;
    }
    if (tail.startsWith(prefix)) {
        return tail;
    }
    return prefix + tail;
}

function paintName() {
    finalName.textContent = campaignName(nameInput.value);
}

async function fillSelect(url, select, emptyText, required) {
    const items = await api(url);
    if (!items.length) {
        select.required = false;
        select.disabled = true;
        select.innerHTML = `<option value="">${emptyText}</option>`;
        return;
    }
    select.disabled = false;
    select.required = required;
    select.innerHTML = items.map((item) => `<option value="${item.id}">${esc(item.name)}</option>`).join("");
}

function selectedId(select) {
    if (select.disabled || !select.value) {
        return null;
    }
    return Number(select.value);
}

nameInput.addEventListener("input", paintName);
geoInput.addEventListener("input", () => {
    geoInput.value = geoInput.value.toUpperCase();
});

offerInput.addEventListener("input", () => {
    picked = null;
    clearTimeout(offerInput._timer);
    offerInput._timer = setTimeout(() => fillOffers(offerInput.value), 250);
});

offerList.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-id]");
    if (!button) {
        return;
    }
    picked = { id: Number(button.dataset.id), name: button.dataset.name };
    offerInput.value = button.dataset.name;
    offerList.hidden = true;
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    clearError();
    const button = form.querySelector("button[type=submit]");
    if (!picked) {
        showError(new Error("Выберите оффер из списка"));
        return;
    }
    button.disabled = true;
    try {
        const body = {
            name: nameInput.value,
            geo: geoInput.value,
            offer_id: picked.id,
            group_id: Number(document.querySelector("#group").value),
        };
        const domainId = selectedId(document.querySelector("#domain"));
        const sourceId = selectedId(document.querySelector("#source"));
        if (domainId) {
            body.domain_id = domainId;
        }
        if (sourceId) {
            body.traffic_source_id = sourceId;
        }
        const created = await api("api/campaigns", {
            method: "POST",
            body,
        });
        location.href = `campaign?id=${created.id}`;
    } catch (error) {
        showError(error);
        button.disabled = false;
    }
});

async function fillOffers(query) {
    if (!query.trim()) {
        offerList.hidden = true;
        return;
    }
    try {
        const items = await api(`api/offers?q=${encodeURIComponent(query)}`);
        if (!items.length) {
            offerList.innerHTML = "<li class=\"muted\">Ничего не найдено</li>";
            offerList.hidden = false;
            return;
        }
        offerList.innerHTML = items.map((item) => (
            `<li><button type="button" data-id="${item.id}" data-name="${esc(item.name)}">${esc(item.name)} <span class="muted">#${item.id}</span></button></li>`
        )).join("");
        offerList.hidden = false;
    } catch (error) {
        showError(error);
    }
}

async function start() {
    try {
        const meta = await api("api/prefix");
        prefix = meta.prefix;
        paintName();
        await Promise.all([
            fillSelect("api/domains", document.querySelector("#domain"), "В трекере нет доменов", false),
            fillSelect("api/groups", document.querySelector("#group"), "В трекере нет групп", true),
            fillSelect("api/sources", document.querySelector("#source"), "В трекере нет источников", false),
        ]);
    } catch (error) {
        showError(error);
    } finally {
        document.querySelector("#form-skeleton").hidden = true;
        form.hidden = false;
    }
}

paintName();
start();
