import pytest

from app.payloads import push_payload
from app.shares import (
    OfferRow,
    ShareError,
    add_offer,
    assert_pushable,
    cancel,
    distribute,
    is_dirty,
    remove_offer,
    restore_offer,
    set_pin,
    sync_offers,
)


def row(
    offer_id: int,
    share: int = 0,
    pinned: bool = False,
    status: str = "active",
    position: int = 0,
    baseline_status: str = "active",
    baseline_share: int | None = 0,
    baseline_pinned: bool = False,
) -> OfferRow:
    return OfferRow(
        offer_id=offer_id,
        name=f"offer-{offer_id}",
        share=share,
        pinned=pinned,
        status=status,
        baseline_share=baseline_share,
        baseline_status=baseline_status,
        baseline_pinned=baseline_pinned,
        position=position,
    )


def shares(rows: list[OfferRow]) -> list[int]:
    return [item.share for item in sorted(rows, key=lambda item: item.position)]


def test_three_offers_split_remainder_to_the_last():
    rows = [row(1, position=0), row(2, position=1), row(3, position=2)]
    distribute(rows)
    assert shares(rows) == [33, 33, 34]


def test_single_offer_takes_all():
    rows = [row(1)]
    distribute(rows)
    assert shares(rows) == [100]


def test_pin_keeps_its_share_until_the_next_change():
    rows = [row(1, 33, position=0), row(2, 33, position=1), row(3, 34, position=2)]
    set_pin(rows, 1, True, 25)
    assert shares(rows) == [25, 33, 34]
    with pytest.raises(ShareError):
        assert_pushable(rows)


def test_add_recalculates_unpinned_and_leaves_the_pin():
    rows = [
        row(1, 25, pinned=True, position=0),
        row(2, 37, position=1),
        row(3, 38, position=2),
    ]
    add_offer(rows, 4, "offer-4")
    assert [(item.offer_id, item.share, item.pinned) for item in rows] == [
        (1, 25, True),
        (2, 25, False),
        (3, 25, False),
        (4, 25, False),
    ]


def test_remove_zeroes_share_and_resplits_the_rest():
    rows = [row(1, 33, position=0), row(2, 33, position=1), row(3, 34, position=2)]
    remove_offer(rows, 3)
    removed = next(item for item in rows if item.offer_id == 3)
    assert removed.status == "removed"
    assert removed.share == 0
    assert shares(rows) == [50, 50, 0]


def test_restore_gets_an_equal_unpinned_share():
    rows = [
        row(1, 25, pinned=True, position=0),
        row(2, 75, position=1),
        row(3, 0, status="removed", position=2),
    ]
    restore_offer(rows, 3)
    assert [(item.offer_id, item.share) for item in rows] == [(1, 25), (2, 37), (3, 38)]


def test_add_is_blocked_when_pins_already_take_everything():
    rows = [row(1, 100, pinned=True)]
    with pytest.raises(ShareError):
        add_offer(rows, 2, "offer-2")


def test_cancel_drops_unpublished_offers_and_restores_the_rest():
    rows = [
        row(1, 100, baseline_share=50, baseline_status="active"),
        row(2, 0, status="active", baseline_status="absent", baseline_share=None),
    ]
    kept = cancel(rows)
    assert [item.offer_id for item in kept] == [1]
    assert kept[0].share == 50
    assert is_dirty(kept) is False


def test_sync_marks_missing_offers_removed_without_deleting_them():
    local = [row(1, 50, position=0), row(2, 50, position=1)]
    synced = sync_offers(local, [(1, 100, "offer-1")])
    by_id = {item.offer_id: item for item in synced}
    assert by_id[1].status == "active"
    assert by_id[1].share == 100
    assert by_id[2].status == "removed"
    assert by_id[2].share == 0
    assert by_id[2].baseline_status == "removed"


def test_push_payload_keeps_filters_and_sends_only_active_offers():
    payload = push_payload(
        {
            "id": 9,
            "name": "AU",
            "schema": "redirect",
            "filters": [{"name": "country", "mode": "accept", "payload": ["AU"]}],
            "action_payload": "https://google.com",
        },
        [(4, 60), (5, 40)],
    )
    assert "id" not in payload
    assert payload["filters"] == [{"name": "country", "mode": "accept", "payload": ["AU"]}]
    assert payload["action_payload"] == "https://google.com"
    assert payload["offers"] == [
        {"offer_id": 4, "share": 60, "state": "active"},
        {"offer_id": 5, "share": 40, "state": "active"},
    ]
