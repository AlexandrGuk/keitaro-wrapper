const params = new URLSearchParams(location.search);
const campaignId = params.get("id");
const title = document.querySelector("#title");
const streamsEl = document.querySelector("#streams");
const fetchBtn = document.querySelector("#fetch");
const ktLink = document.querySelector("#kt-link");

let state = { streams: [] };
let busy = false;

function statsLine(stats) {
    return `${stats.clicks} кликов<br>${stats.conversions} конв.<br>${stats.cr}% CR<br>$${stats.revenue}`;
}

function trendBars(values) {
    const series = values && values.length ? values : [0, 0, 0, 0, 0, 0, 0];
    const max = Math.max(...series, 1);
    const bars = series.map((value) => {
        const height = Math.max(2, Math.round((value / max) * 28));
        return `<i style="height:${height}px" title="${value}"></i>`;
    }).join("");
    return `<span class="trend" aria-label="Клики за 7 дней">${bars}</span>`;
}

function offerRow(offer) {
    const removed = offer.status === "removed";
    const stats = offer.stats || { clicks: 0, conversions: 0, cr: 0, revenue: 0, trend: [] };
    const share = offer.pinned && !removed
        ? `<input data-share="${offer.offer_id}" type="number" min="0" max="100" value="${offer.share}">`
        : `${offer.share}%`;
    const actions = removed
        ? `<button type="button" class="btn" data-action="restore" data-offer="${offer.offer_id}">Вернуть</button>`
        : `<button type="button" class="btn" data-action="${offer.pinned ? "unpin" : "pin"}" data-offer="${offer.offer_id}" data-current="${offer.share}">${offer.pinned ? "Открепить" : "Закрепить"}</button>
           <button type="button" class="btn" data-action="remove" data-offer="${offer.offer_id}">Удалить</button>`;
    return `<tr class="${removed ? "is-removed" : ""}">
        <td>${esc(offer.name)} <span class="muted">#${offer.offer_id}</span></td>
        <td>${share}</td>
        <td class="stats">${statsLine(stats)}</td>
        <td>${trendBars(stats.trend)}</td>
        <td class="actions">${actions}</td>
    </tr>`;
}

function render() {
    document.querySelector("#skeleton").hidden = true;
    streamsEl.hidden = false;
    if (!state.streams.length) {
        streamsEl.innerHTML = "<section class=\"window\"><p class=\"muted\">Потоков нет.</p></section>";
        return;
    }
    streamsEl.innerHTML = state.streams.map((stream, index) => {
        const number = index + 1;
        const role = number === 1
            ? "Поток 1 ловит указанные страны и отправляет их на Google."
            : number === 2
                ? "Поток 2 отправляет на офферы всех, кого не забрал первый поток."
                : "";
        const bad = stream.offers.some((offer) => offer.status === "active") && stream.share_total !== 100;
        const rows = stream.offers.map(offerRow).join("");
        const editor = stream.editable
            ? `<p class="sum${bad ? " sum-bad" : ""}">Сумма долей: ${stream.share_total}</p>
               <table>
                   <thead><tr><th>Оффер</th><th>Доля</th><th>Stats</th><th>Trends</th><th></th></tr></thead>
                   <tbody>${rows || "<tr><td colspan=\"5\" class=\"muted\">Офферов нет</td></tr>"}</tbody>
               </table>
               <div class="suggest">
                   <label class="pixel" for="search-${stream.id}">Добавить оффер</label>
                   <input id="search-${stream.id}" data-search type="text" autocomplete="off" placeholder="имя или id">
                   <ul class="suggest-list" hidden></ul>
               </div>
               <div class="actions">
                   <button class="btn btn-primary" type="button" data-action="add">Добавить</button>
                   ${stream.dirty ? "<button class=\"btn btn-primary\" type=\"button\" data-action=\"push\">Опубликовать</button><button class=\"btn\" type=\"button\" data-action=\"cancel\">Отменить</button>" : ""}
               </div>`
            : `<p class="muted">${role || "В этом потоке офферов нет."}</p>`;
        return `<section class="window${stream.dirty ? " is-dirty" : ""}" data-stream="${stream.id}">
            <h2 class="window-title">Поток ${number}. ${esc(stream.name || "Поток")}${stream.dirty ? " <span class=\"badge\">не опубликовано</span>" : ""}</h2>
            ${role && stream.editable ? `<p class="muted stream-role">${role}</p>` : ""}
            ${editor}
        </section>`;
    }).join("");
}

async function run(work) {
    if (busy) {
        return;
    }
    busy = true;
    clearError();
    try {
        await work();
    } catch (error) {
        showError(error);
    } finally {
        busy = false;
    }
}

async function fillSuggest(section, query) {
    const list = section.querySelector(".suggest-list");
    if (!query.trim()) {
        list.hidden = true;
        return;
    }
    const items = await api(`api/offers?q=${encodeURIComponent(query)}`);
    if (!items.length) {
        list.innerHTML = "<li class=\"muted\">Ничего не найдено</li>";
        list.hidden = false;
        return;
    }
    list.innerHTML = items.map((item) => (
        `<li><button type="button" data-action="pick" data-id="${item.id}" data-name="${esc(item.name)}">${esc(item.name)} <span class="muted">#${item.id}</span></button></li>`
    )).join("");
    list.hidden = false;
}

streamsEl.addEventListener("input", (event) => {
    const input = event.target.closest("[data-search]");
    if (!input) {
        return;
    }
    const section = input.closest("[data-stream]");
    delete section.dataset.picked;
    clearTimeout(input._timer);
    input._timer = setTimeout(() => {
        fillSuggest(section, input.value).catch(showError);
    }, 250);
});

streamsEl.addEventListener("change", (event) => {
    const input = event.target.closest("[data-share]");
    if (!input) {
        return;
    }
    const section = input.closest("[data-stream]");
    run(async () => {
        state = await api(
            `api/campaigns/${campaignId}/streams/${section.dataset.stream}/offers/${input.dataset.share}/pin`,
            { method: "POST", body: { pinned: true, share: Number(input.value) } },
        );
        render();
    });
});

streamsEl.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) {
        return;
    }
    const section = button.closest("[data-stream]");
    const action = button.dataset.action;
    if (!section || !action) {
        return;
    }
    if (action === "pick") {
        section.dataset.picked = button.dataset.id;
        section.querySelector("[data-search]").value = button.dataset.name;
        section.querySelector(".suggest-list").hidden = true;
        return;
    }
    const streamId = section.dataset.stream;
    run(async () => {
        if (action === "add") {
            if (!section.dataset.picked) {
                throw new Error("Выберите оффер из списка");
            }
            state = await api(`api/campaigns/${campaignId}/streams/${streamId}/offers`, {
                method: "POST",
                body: { offer_id: Number(section.dataset.picked) },
            });
        } else if (action === "pin" || action === "unpin") {
            state = await api(
                `api/campaigns/${campaignId}/streams/${streamId}/offers/${button.dataset.offer}/pin`,
                {
                    method: "POST",
                    body: {
                        pinned: action === "pin",
                        share: action === "pin" ? Number(button.dataset.current) : null,
                    },
                },
            );
        } else if (action === "remove" || action === "restore") {
            state = await api(
                `api/campaigns/${campaignId}/streams/${streamId}/offers/${button.dataset.offer}/${action}`,
                { method: "POST" },
            );
        } else if (action === "push" || action === "cancel") {
            state = await api(
                `api/campaigns/${campaignId}/streams/${streamId}/${action}`,
                { method: "POST" },
            );
        }
        render();
    });
});

fetchBtn.addEventListener("click", () => {
    if (state.streams.some((stream) => stream.dirty) && !confirm("Неопубликованные правки будут заменены данными из Keitaro.")) {
        return;
    }
    document.querySelector("#skeleton").hidden = false;
    streamsEl.hidden = true;
    run(async () => {
        try {
            state = await api(`api/campaigns/${campaignId}/fetch`, { method: "POST" });
            render();
        } catch (error) {
            document.querySelector("#skeleton").hidden = true;
            streamsEl.hidden = false;
            throw error;
        }
    });
});

document.querySelector("#delete-campaign").addEventListener("click", () => {
    const name = title.textContent || "эту кампанию";
    if (!confirm(`Удалить кампанию ${name}? В Keitaro она уйдёт в архив.`)) {
        return;
    }
    run(async () => {
        await api(`api/campaigns/${campaignId}`, { method: "DELETE" });
        location.href = "campaigns";
    });
});

async function start() {
    if (!campaignId) {
        showError(new Error("Не передан id кампании"));
        return;
    }
    try {
        const campaign = await api(`api/campaigns/${campaignId}`);
        title.textContent = campaign.name;
        document.title = campaign.name;
        ktLink.href = campaign.admin_url;
        const local = await api(`api/campaigns/${campaignId}/streams`);
        state = local.streams.length
            ? local
            : await api(`api/campaigns/${campaignId}/fetch`, { method: "POST" });
        render();
    } catch (error) {
        document.querySelector("#skeleton").hidden = true;
        showError(error);
    }
}

start();
