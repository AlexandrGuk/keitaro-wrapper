from datetime import date, timedelta

from app.keitaro import KeitaroClient, KeitaroError

WINDOW_DAYS = 7


def empty_stats() -> dict:
    return {
        "clicks": 0,
        "conversions": 0,
        "cr": 0.0,
        "revenue": 0.0,
        "trend": [0] * WINDOW_DAYS,
    }


def build_stats(summary_rows: list[dict], daily_rows: list[dict], days: list[str]) -> dict[tuple[int, int], dict]:
    index = {day: position for position, day in enumerate(days)}
    result: dict[tuple[int, int], dict] = {}
    for row in summary_rows:
        key = _key(row)
        result[key] = {
            "clicks": int(_number(row.get("clicks"))),
            "conversions": int(_number(row.get("conversions"))),
            "cr": round(_number(row.get("cr")), 2),
            "revenue": round(_number(row.get("revenue")), 2),
            "trend": [0] * len(days),
        }
    for row in daily_rows:
        key = _key(row)
        bucket = result.setdefault(key, empty_stats())
        day = str(row.get("day") or "")[:10]
        if day in index:
            bucket["trend"][index[day]] = int(_number(row.get("clicks")))
    return result


def offer_stats(client: KeitaroClient, campaign_id: int) -> dict[tuple[int, int], dict]:
    end = date.today()
    start = end - timedelta(days=WINDOW_DAYS - 1)
    days = [(start + timedelta(days=offset)).isoformat() for offset in range(WINDOW_DAYS)]
    try:
        summary = _rows(client, campaign_id, ["stream_id", "offer_id"], ["clicks", "conversions", "cr", "revenue"], start, end)
    except KeitaroError:
        return {}
    try:
        daily = _rows(client, campaign_id, ["stream_id", "offer_id", "day"], ["clicks"], start, end)
    except KeitaroError:
        daily = []
    return build_stats(summary, daily, days)


def _rows(client: KeitaroClient, campaign_id: int, dimensions: list[str], metrics: list[str], start: date, end: date) -> list[dict]:
    data = client.report(
        {
            "range": {"from": start.isoformat(), "to": end.isoformat(), "timezone": "Europe/Moscow"},
            "dimensions": dimensions,
            "metrics": metrics,
            "filters": [{"name": "campaign_id", "operator": "EQUALS", "expression": campaign_id}],
        }
    )
    if isinstance(data, dict):
        return data.get("rows") or []
    return data or []


def _key(row: dict) -> tuple[int, int]:
    return int(_number(row.get("stream_id"))), int(_number(row.get("offer_id")))


def _number(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
