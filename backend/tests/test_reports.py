from app.reports import build_stats


def test_stats_follow_the_reported_days():
    days = ["2026-11-11", "2026-11-12", "2026-11-13"]
    stats = build_stats(
        [{"stream_id": 4, "offer_id": 9, "clicks": 12, "conversions": 2, "cr": 16.666, "revenue": 4.5}],
        [
            {"stream_id": 4, "offer_id": 9, "day": "2026-11-11", "clicks": 2},
            {"stream_id": 4, "offer_id": 9, "day": "2026-11-13", "clicks": 10},
        ],
        days,
    )
    assert stats[(4, 9)]["clicks"] == 12
    assert stats[(4, 9)]["conversions"] == 2
    assert stats[(4, 9)]["cr"] == 16.67
    assert stats[(4, 9)]["revenue"] == 4.5
    assert stats[(4, 9)]["trend"] == [2, 0, 10]
