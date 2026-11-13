import re

from app.config import settings
from app.keitaro import KeitaroClient
from app.naming import NamingError, campaign_name

_GEO = re.compile(r"^[A-Z]{2}$")
GOOGLE = "https://google.com"


def parse_geos(raw: str) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[\s,;]+", raw.strip().upper()):
        if not part:
            continue
        if not _GEO.fullmatch(part):
            raise NamingError("Гео-код — две латинские буквы, несколько через запятую")
        if part not in seen:
            seen.add(part)
            codes.append(part)
    if not codes:
        raise NamingError("Укажите хотя бы одну страну")
    return codes


def create_campaign(
    client: KeitaroClient,
    raw_name: str,
    geo: str,
    offer_id: int,
    group_id: int,
    domain_id: int | None = None,
    traffic_source_id: int | None = None,
) -> dict:
    codes = parse_geos(geo)
    name = campaign_name(raw_name, settings.campaign_prefix)
    _require_choice(client.groups() or [], group_id, "Группа не найдена")
    if domain_id is not None:
        _require_choice(client.domains() or [], domain_id, "Домен не найден")
    if traffic_source_id is not None:
        _require_choice(client.traffic_sources() or [], traffic_source_id, "Источник не найден")
    offer = client.offer(offer_id)
    if not offer or offer.get("state") == "deleted":
        raise NamingError("Оффер не найден")
    for existing in client.campaigns() or []:
        existing_name = (existing.get("name") or "").lower()
        existing_alias = (existing.get("alias") or "").lower()
        if existing_name == name or existing_alias == name:
            raise NamingError("Кампания с таким именем уже есть")

    payload = {
        "name": name,
        "alias": name,
        "type": "position",
        "state": "active",
        "group_id": group_id,
    }
    if domain_id is not None:
        payload["domain_id"] = domain_id
    if traffic_source_id is not None:
        payload["traffic_source_id"] = traffic_source_id
    created = client.create_campaign(payload)
    campaign_id = int(created["id"])
    try:
        client.create_stream(_geo_stream(campaign_id, codes))
        client.create_stream(_offer_stream(campaign_id, offer_id))
    except Exception:
        try:
            client.delete_campaign(campaign_id)
        except Exception:
            pass
        raise
    created["name"] = name
    return created


def _require_choice(rows: list[dict], item_id: int, message: str) -> None:
    for row in rows:
        if int(row.get("id") or 0) == item_id and row.get("state") != "deleted":
            return
    raise NamingError(message)


def _geo_stream(campaign_id: int, geos: list[str]) -> dict:
    label = ",".join(geos)
    return {
        "campaign_id": campaign_id,
        "type": "regular",
        "name": f"{label} -> Google",
        "position": 1,
        "weight": 100,
        "schema": "redirect",
        "action_type": "http",
        "action_payload": GOOGLE,
        "state": "active",
        "collect_clicks": True,
        "filter_or": False,
        "filters": [{"name": "country", "mode": "accept", "payload": geos}],
        "triggers": [],
        "landings": [],
        "offers": [],
    }


def _offer_stream(campaign_id: int, offer_id: int) -> dict:
    return {
        "campaign_id": campaign_id,
        "type": "regular",
        "name": "Offers",
        "position": 2,
        "weight": 100,
        "schema": "landings",
        "action_type": "http",
        "action_payload": "",
        "state": "active",
        "collect_clicks": True,
        "filter_or": False,
        "filters": [],
        "triggers": [],
        "landings": [],
        "offers": [{"offer_id": offer_id, "share": 100, "state": "active"}],
    }
