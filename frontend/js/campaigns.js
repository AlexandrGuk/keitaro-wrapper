const list = document.querySelector("#list");
const empty = document.querySelector("#empty");
const skeleton = document.querySelector("#skeleton");

function finishLoading() {
    skeleton.hidden = true;
}

async function start() {
    try {
        const items = await api("api/campaigns");
        finishLoading();
        if (!items.length) {
            empty.hidden = false;
            return;
        }
        list.hidden = false;
        list.innerHTML = items.map((item) => (
            `<li><a href="campaign?id=${item.id}">${esc(item.name)}</a></li>`
        )).join("");
    } catch (error) {
        finishLoading();
        showError(error);
    }
}

start();
