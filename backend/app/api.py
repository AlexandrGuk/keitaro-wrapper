import secrets
from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.creator import create_campaign
from app.db import SessionLocal
from app.editor import (
    add_stream_offer,
    cancel_stream,
    delete_campaign_state,
    fetch_streams,
    guard_campaign,
    list_state,
    pin_stream_offer,
    push_stream,
    remove_stream_offer,
    restore_stream_offer,
)
from app.keitaro import KeitaroClient

router = APIRouter()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_client() -> KeitaroClient:
    if not settings.keitaro_base_url or not settings.keitaro_api_key:
        raise HTTPException(
            status_code=500,
            detail="Заполните KEITARO_BASE_URL и KEITARO_API_KEY в backend/.env",
        )
    return KeitaroClient(settings.keitaro_base_url, settings.keitaro_api_key)


class CreateIn(BaseModel):
    name: str = Field(min_length=1)
    geo: str
    offer_id: int = Field(gt=0)
    group_id: int = Field(gt=0)
    domain_id: int | None = None
    traffic_source_id: int | None = None


class OfferIn(BaseModel):
    offer_id: int = Field(gt=0)


class PinIn(BaseModel):
    pinned: bool
    share: int | None = None


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginIn, request: Request) -> dict:
    username_ok = secrets.compare_digest(body.username, settings.app_username)
    password_ok = bool(settings.app_password) and secrets.compare_digest(body.password, settings.app_password)
    if not (username_ok and password_ok):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    request.session["user"] = settings.app_username
    return {"ok": True}


@router.post("/logout")
def logout(request: Request) -> dict:
    request.session.clear()
    return {"ok": True}


@router.get("/prefix")
def prefix() -> dict:
    return {"prefix": settings.campaign_prefix}


@router.get("/domains")
def domains(client: KeitaroClient = Depends(get_client)) -> list[dict]:
    return _refs(client.domains())


@router.get("/groups")
def groups(client: KeitaroClient = Depends(get_client)) -> list[dict]:
    return _refs(client.groups())


@router.get("/sources")
def sources(client: KeitaroClient = Depends(get_client)) -> list[dict]:
    return _refs(client.traffic_sources())


@router.get("/offers")
def offers(q: str = "", client: KeitaroClient = Depends(get_client)) -> list[dict]:
    query = q.strip().lower()
    found = []
    for row in client.offers() or []:
        if row.get("state") == "deleted":
            continue
        offer_id = int(row["id"])
        name = row.get("name") or ""
        if query and query not in name.lower() and query not in str(offer_id):
            continue
        found.append({"id": offer_id, "name": name})
        if len(found) >= 20:
            break
    return found


@router.get("/campaigns")
def campaigns(client: KeitaroClient = Depends(get_client)) -> list[dict]:
    items = []
    for row in client.campaigns() or []:
        name = row.get("name") or ""
        if row.get("state") == "deleted" or not name.startswith(settings.campaign_prefix):
            continue
        items.append(_campaign_out(row))
    items.sort(key=lambda item: item["id"], reverse=True)
    return items


@router.post("/campaigns")
def create(body: CreateIn, client: KeitaroClient = Depends(get_client)) -> dict:
    created = create_campaign(
        client,
        body.name,
        body.geo,
        body.offer_id,
        body.group_id,
        body.domain_id,
        body.traffic_source_id,
    )
    return _campaign_out(created)


@router.get("/campaigns/{campaign_id}")
def campaign(campaign_id: int, client: KeitaroClient = Depends(get_client)) -> dict:
    return _campaign_out(guard_campaign(client, campaign_id))


@router.delete("/campaigns/{campaign_id}")
def remove_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    delete_campaign_state(db, client, campaign_id)
    return {"ok": True}


@router.get("/campaigns/{campaign_id}/streams")
def streams(
    campaign_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return list_state(db, client, campaign_id)


@router.post("/campaigns/{campaign_id}/fetch")
def fetch(campaign_id: int, db: Session = Depends(get_db), client: KeitaroClient = Depends(get_client)) -> dict:
    return fetch_streams(db, client, campaign_id)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/offers")
def add_offer(
    campaign_id: int,
    stream_id: int,
    body: OfferIn,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return add_stream_offer(db, client, campaign_id, stream_id, body.offer_id)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/offers/{offer_id}/remove")
def remove_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return remove_stream_offer(db, client, campaign_id, stream_id, offer_id)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/offers/{offer_id}/restore")
def restore_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return restore_stream_offer(db, client, campaign_id, stream_id, offer_id)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/offers/{offer_id}/pin")
def pin_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    body: PinIn,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return pin_stream_offer(db, client, campaign_id, stream_id, offer_id, body.pinned, body.share)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/cancel")
def cancel(
    campaign_id: int,
    stream_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return cancel_stream(db, client, campaign_id, stream_id)


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/push")
def push(
    campaign_id: int,
    stream_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_client),
) -> dict:
    return push_stream(db, client, campaign_id, stream_id)


def _campaign_out(row: dict) -> dict:
    campaign_id = int(row["id"])
    return {
        "id": campaign_id,
        "name": row.get("name") or "",
        "alias": row.get("alias") or "",
        "state": row.get("state") or "",
        "admin_url": f"{settings.keitaro_base_url}/admin/#!/campaigns/{campaign_id}/streams",
    }


def _refs(rows: list[dict] | None) -> list[dict]:
    items = []
    for row in rows or []:
        if row.get("state") == "deleted":
            continue
        items.append({"id": int(row["id"]), "name": row.get("name") or str(row["id"])})
    items.sort(key=lambda item: item["name"].lower())
    return items
