import pytest

from app.creator import parse_geos
from app.naming import NamingError


def test_parses_several_geos():
    assert parse_geos("mx, AU;ro") == ["MX", "AU", "RO"]


def test_drops_duplicate_geos():
    assert parse_geos("AU,AU, MX") == ["AU", "MX"]


def test_rejects_a_broken_code():
    with pytest.raises(NamingError):
        parse_geos("AU,MEX")
