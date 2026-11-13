_KEEP = (
    "campaign_id",
    "type",
    "name",
    "position",
    "weight",
    "action_options",
    "comments",
    "state",
    "action_type",
    "action_payload",
    "schema",
    "collect_clicks",
    "filter_or",
    "filters",
    "triggers",
    "landings",
    "offer_selection",
)


def push_payload(raw: dict, offers: list[tuple[int, int]]) -> dict:
    payload = {key: raw[key] for key in _KEEP if key in raw and raw[key] is not None}
    payload["offers"] = [
        {"offer_id": offer_id, "share": share, "state": "active"}
        for offer_id, share in offers
    ]
    payload.setdefault("filters", [])
    payload.setdefault("landings", [])
    payload.setdefault("triggers", [])
    return payload
