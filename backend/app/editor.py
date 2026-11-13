import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.keitaro import KeitaroClient, KeitaroError
from app.models import Stream, StreamOffer
from app.naming import NamingError
from app.payloads import push_payload
from app.reports import empty_stats, offer_stats
from app.shares import (
    OfferRow,
    ShareError,
    add_offer,
    assert_pushable,
    cancel,
    is_dirty,
    mark_synced,
    remove_offer,
    restore_offer,
    set_pin,
    sync_offers,
)


class NotFound(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def delete_campaign_state(db: Session, client: KeitaroClient, campaign_id: int) -> None:
    guard_campaign(client, campaign_id)
    client.delete_campaign(campaign_id)
    for stream in db.scalars(select(Stream).where(Stream.keitaro_campaign_id == campaign_id)).all():
        db.delete(stream)
    db.commit()


def list_state(db: Session, client: KeitaroClient, campaign_id: int) -> dict:
    streams = db.scalars(
        select(Stream)
        .where(Stream.keitaro_campaign_id == campaign_id)
        .order_by(Stream.position, Stream.id)
    ).all()
    payload = {"streams": [serialize_stream(stream) for stream in streams]}
    found = offer_stats(client, campaign_id)
    for stream in payload["streams"]:
        for offer in stream["offers"]:
            offer["stats"] = found.get((stream["keitaro_stream_id"], offer["offer_id"]), empty_stats())
    return payload


def fetch_streams(db: Session, client: KeitaroClient, campaign_id: int) -> dict:
    guard_campaign(client, campaign_id)
    remote_streams = client.campaign_streams(campaign_id) or []
    names = _offer_names(client)
    incoming: set[int] = set()
    for raw in remote_streams:
        stream_id = int(raw["id"])
        incoming.add(stream_id)
        stream = db.scalar(select(Stream).where(Stream.keitaro_stream_id == stream_id))
        if stream is None:
            stream = Stream(keitaro_campaign_id=campaign_id, keitaro_stream_id=stream_id)
            db.add(stream)
        stream.keitaro_campaign_id = campaign_id
        stream.name = raw.get("name") or ""
        stream.stream_type = raw.get("type") or ""
        stream.position = int(raw.get("position") or 0)
        stream.schema_name = raw.get("schema") or ""
        stream.raw_json = json.dumps(raw, ensure_ascii=False)
        remote = [
            (
                int(item["offer_id"]),
                int(item.get("share") or 0),
                names.get(int(item["offer_id"]), f"#{item['offer_id']}"),
            )
            for item in (raw.get("offers") or [])
        ]
        synced = sync_offers([_to_row(offer) for offer in stream.offers], remote)
        _replace_offers(stream, synced)
        stream.dirty = False
    stale = db.scalars(select(Stream).where(Stream.keitaro_campaign_id == campaign_id)).all()
    for stream in stale:
        if stream.keitaro_stream_id not in incoming:
            db.delete(stream)
    db.commit()
    return list_state(db, client, campaign_id)


def add_stream_offer(
    db: Session,
    client: KeitaroClient,
    campaign_id: int,
    stream_id: int,
    offer_id: int,
) -> dict:
    guard_campaign(client, campaign_id)
    stream = _load_stream(db, campaign_id, stream_id)
    _ensure_editable(stream)
    offer = client.offer(offer_id)
    if not offer or offer.get("state") == "deleted":
        raise NamingError("Оффер не найден")
    rows = [_to_row(item) for item in stream.offers]
    add_offer(rows, offer_id, offer.get("name") or f"#{offer_id}")
    _save(db, stream, rows)
    return list_state(db, client, campaign_id)


def remove_stream_offer(db: Session, client: KeitaroClient, campaign_id: int, stream_id: int, offer_id: int) -> dict:
    return _change(db, client, campaign_id, stream_id, lambda rows: remove_offer(rows, offer_id))


def restore_stream_offer(db: Session, client: KeitaroClient, campaign_id: int, stream_id: int, offer_id: int) -> dict:
    return _change(db, client, campaign_id, stream_id, lambda rows: restore_offer(rows, offer_id))


def pin_stream_offer(
    db: Session,
    client: KeitaroClient,
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    pinned: bool,
    share: int | None,
) -> dict:
    return _change(
        db,
        client,
        campaign_id,
        stream_id,
        lambda rows: set_pin(rows, offer_id, pinned, share),
    )


def cancel_stream(db: Session, client: KeitaroClient, campaign_id: int, stream_id: int) -> dict:
    guard_campaign(client, campaign_id)
    stream = _load_stream(db, campaign_id, stream_id)
    rows = cancel([_to_row(item) for item in stream.offers])
    _save(db, stream, rows)
    return list_state(db, client, campaign_id)


def push_stream(db: Session, client: KeitaroClient, campaign_id: int, stream_id: int) -> dict:
    guard_campaign(client, campaign_id)
    stream = _load_stream(db, campaign_id, stream_id)
    rows = [_to_row(item) for item in stream.offers]
    if not is_dirty(rows):
        stream.dirty = False
        db.commit()
        return list_state(db, client, campaign_id)
    assert_pushable(rows)
    active_rows = sorted(
        (row for row in rows if row.status == "active"),
        key=lambda row: (row.position, row.offer_id),
    )
    raw = json.loads(stream.raw_json or "{}")
    client.update_stream(
        stream.keitaro_stream_id,
        push_payload(raw, [(row.offer_id, row.share) for row in active_rows]),
    )
    fresh = client.stream(stream.keitaro_stream_id)
    if not isinstance(fresh, dict):
        raise KeitaroError(502, "Keitaro не вернул поток")
    stream.raw_json = json.dumps(fresh, ensure_ascii=False)
    stream.name = fresh.get("name") or stream.name
    stream.schema_name = fresh.get("schema") or stream.schema_name
    mark_synced(rows)
    _replace_offers(stream, rows)
    stream.dirty = False
    db.commit()
    return list_state(db, client, campaign_id)


def guard_campaign(client: KeitaroClient, campaign_id: int) -> dict:
    campaign = client.campaign(campaign_id)
    name = campaign.get("name") or ""
    if not name.startswith(settings.campaign_prefix):
        raise NotFound("Кампания не входит в тестовый префикс")
    return campaign


def serialize_stream(stream: Stream) -> dict:
    offers = sorted(stream.offers, key=lambda offer: (offer.position, offer.id))
    return {
        "id": stream.id,
        "keitaro_stream_id": stream.keitaro_stream_id,
        "name": stream.name,
        "type": stream.stream_type,
        "stream_schema": stream.schema_name,
        "position": stream.position,
        "dirty": stream.dirty,
        "editable": bool(offers) or stream.schema_name != "redirect",
        "share_total": sum(offer.share for offer in offers if offer.status == "active"),
        "offers": [
            {
                "id": offer.id,
                "offer_id": offer.offer_id,
                "name": offer.name,
                "share": offer.share,
                "pinned": offer.pinned,
                "status": offer.status,
            }
            for offer in offers
        ],
    }


def _change(db: Session, client: KeitaroClient, campaign_id: int, stream_id: int, action) -> dict:
    guard_campaign(client, campaign_id)
    stream = _load_stream(db, campaign_id, stream_id)
    _ensure_editable(stream)
    rows = [_to_row(item) for item in stream.offers]
    action(rows)
    _save(db, stream, rows)
    return list_state(db, client, campaign_id)


def _save(db: Session, stream: Stream, rows: list[OfferRow]) -> None:
    _replace_offers(stream, rows)
    stream.dirty = is_dirty(rows)
    db.commit()


def _ensure_editable(stream: Stream) -> None:
    if stream.offers or stream.schema_name != "redirect":
        return
    raise ShareError("У этого потока нет офферов, состав не меняем")


def _load_stream(db: Session, campaign_id: int, stream_id: int) -> Stream:
    stream = db.get(Stream, stream_id)
    if stream is None or stream.keitaro_campaign_id != campaign_id:
        raise NotFound("Поток не найден")
    return stream


def _offer_names(client: KeitaroClient) -> dict[int, str]:
    names: dict[int, str] = {}
    for offer in client.offers() or []:
        names[int(offer["id"])] = offer.get("name") or f"#{offer['id']}"
    return names


def _replace_offers(stream: Stream, rows: list[OfferRow]) -> None:
    by_id = {offer.offer_id: offer for offer in stream.offers}
    seen: set[int] = set()
    for row in rows:
        model = by_id.get(row.offer_id)
        if model is None:
            model = StreamOffer(offer_id=row.offer_id)
            stream.offers.append(model)
        _apply_row(model, row)
        seen.add(row.offer_id)
    for offer in list(stream.offers):
        if offer.offer_id not in seen:
            stream.offers.remove(offer)


def _to_row(offer: StreamOffer) -> OfferRow:
    return OfferRow(
        offer_id=offer.offer_id,
        name=offer.name,
        share=offer.share,
        pinned=offer.pinned,
        status=offer.status,
        baseline_share=offer.baseline_share,
        baseline_status=offer.baseline_status,
        baseline_pinned=offer.baseline_pinned,
        position=offer.position,
    )


def _apply_row(offer: StreamOffer, row: OfferRow) -> None:
    offer.name = row.name
    offer.share = row.share
    offer.pinned = row.pinned
    offer.status = row.status
    offer.baseline_share = row.baseline_share
    offer.baseline_status = row.baseline_status
    offer.baseline_pinned = row.baseline_pinned
    offer.position = row.position
