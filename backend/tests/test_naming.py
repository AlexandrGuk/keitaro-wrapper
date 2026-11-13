import pytest

from app.naming import NamingError, campaign_name


def test_adds_prefix():
    assert campaign_name("campaign1", "test_guk_") == "test_guk_campaign1"


def test_keeps_existing_prefix():
    assert campaign_name("test_guk_campaign1", "test_guk_") == "test_guk_campaign1"


def test_normalizes_spaces_and_case():
    assert campaign_name("Campaign 1", "test_guk_") == "test_guk_campaign_1"


def test_rejects_empty_tail():
    with pytest.raises(NamingError):
        campaign_name("!!!", "test_guk_")
