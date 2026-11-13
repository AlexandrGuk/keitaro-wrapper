from dataclasses import dataclass


class ShareError(Exception):
    pass


@dataclass
class OfferRow:
    offer_id: int
    name: str
    share: int
    pinned: bool
    status: str
    baseline_share: int | None
    baseline_status: str
    baseline_pinned: bool
    position: int


def distribute(rows: list[OfferRow]) -> None:
    for row in rows:
        if row.status != "active":
            row.share = 0
            row.pinned = False
    active = sorted(
        (row for row in rows if row.status == "active"),
        key=lambda row: (row.position, row.offer_id),
    )
    pinned = [row for row in active if row.pinned]
    unpinned = [row for row in active if not row.pinned]
    remainder = 100 - sum(row.share for row in pinned)
    if remainder < 0 or not unpinned:
        for row in unpinned:
            row.share = 0
        return
    base, extra = divmod(remainder, len(unpinned))
    first_extra = len(unpinned) - extra
    for index, row in enumerate(unpinned):
        row.share = base + (1 if index >= first_extra else 0)


def _active_pinned_sum(rows: list[OfferRow]) -> int:
    return sum(row.share for row in rows if row.status == "active" and row.pinned)


def _require(rows: list[OfferRow], offer_id: int) -> OfferRow:
    for row in rows:
        if row.offer_id == offer_id:
            return row
    raise ShareError("Оффер не найден в потоке")


def _ensure_room(rows: list[OfferRow]) -> None:
    if _active_pinned_sum(rows) >= 100:
        raise ShareError("Закреплённые доли уже занимают 100%")


def add_offer(rows: list[OfferRow], offer_id: int, name: str) -> None:
    existing = next((row for row in rows if row.offer_id == offer_id), None)
    if existing and existing.status == "active":
        raise ShareError("Оффер уже есть в потоке")
    if existing and existing.status == "removed":
        restore_offer(rows, offer_id)
        return
    _ensure_room(rows)
    position = max((row.position for row in rows), default=-1) + 1
    rows.append(
        OfferRow(
            offer_id=offer_id,
            name=name,
            share=0,
            pinned=False,
            status="active",
            baseline_share=None,
            baseline_status="absent",
            baseline_pinned=False,
            position=position,
        )
    )
    distribute(rows)


def remove_offer(rows: list[OfferRow], offer_id: int) -> None:
    row = _require(rows, offer_id)
    if row.status != "active":
        raise ShareError("Оффер уже удалён")
    row.status = "removed"
    row.share = 0
    row.pinned = False
    distribute(rows)


def restore_offer(rows: list[OfferRow], offer_id: int) -> None:
    row = _require(rows, offer_id)
    if row.status != "removed":
        raise ShareError("Оффер не в архиве")
    _ensure_room(rows)
    row.status = "active"
    row.pinned = False
    row.share = 0
    distribute(rows)


def set_pin(rows: list[OfferRow], offer_id: int, pinned: bool, share: int | None) -> None:
    row = _require(rows, offer_id)
    if row.status != "active":
        raise ShareError("Нельзя закрепить удалённый оффер")
    if not pinned:
        row.pinned = False
        distribute(rows)
        return
    value = row.share if share is None else share
    if value < 0 or value > 100:
        raise ShareError("Доля должна быть от 0 до 100")
    row.share = value
    row.pinned = True


def cancel(rows: list[OfferRow]) -> list[OfferRow]:
    kept: list[OfferRow] = []
    for row in rows:
        if row.baseline_status == "absent":
            continue
        row.status = row.baseline_status
        row.share = 0 if row.baseline_share is None else row.baseline_share
        row.pinned = row.baseline_pinned
        kept.append(row)
    return kept


def is_dirty(rows: list[OfferRow]) -> bool:
    for row in rows:
        if row.baseline_status == "absent":
            return True
        if row.status != row.baseline_status:
            return True
        if row.share != (0 if row.baseline_share is None else row.baseline_share):
            return True
        if row.pinned != row.baseline_pinned:
            return True
    return False


def assert_pushable(rows: list[OfferRow]) -> None:
    active = [row for row in rows if row.status == "active"]
    if not active:
        return
    total = sum(row.share for row in active)
    if total != 100:
        raise ShareError(f"Сумма долей {total}, нужна 100")


def mark_synced(rows: list[OfferRow]) -> None:
    for row in rows:
        if row.status == "active":
            row.baseline_status = "active"
            row.baseline_share = row.share
            row.baseline_pinned = row.pinned
            continue
        row.status = "removed"
        row.share = 0
        row.pinned = False
        row.baseline_status = "removed"
        row.baseline_share = 0
        row.baseline_pinned = False


def sync_offers(local: list[OfferRow], remote: list[tuple[int, int, str]]) -> list[OfferRow]:
    by_id = {row.offer_id: row for row in local}
    remote_ids = {offer_id for offer_id, _share, _name in remote}
    result: list[OfferRow] = []
    for index, (offer_id, share, name) in enumerate(remote):
        row = by_id.get(offer_id)
        if row is None:
            row = OfferRow(
                offer_id=offer_id,
                name=name,
                share=share,
                pinned=False,
                status="active",
                baseline_share=share,
                baseline_status="active",
                baseline_pinned=False,
                position=index,
            )
        else:
            row.name = name or row.name
            row.share = share
            row.pinned = False
            row.status = "active"
            row.baseline_share = share
            row.baseline_status = "active"
            row.baseline_pinned = False
            row.position = index
        result.append(row)
    removed_at = len(remote)
    for row in local:
        if row.offer_id in remote_ids:
            continue
        row.status = "removed"
        row.share = 0
        row.pinned = False
        row.baseline_status = "removed"
        row.baseline_share = 0
        row.baseline_pinned = False
        row.position = removed_at
        removed_at += 1
        result.append(row)
    return result
