import re

_UNSAFE = re.compile(r"[^a-z0-9_]+")
_REPEATS = re.compile(r"_+")


class NamingError(ValueError):
    pass


def campaign_name(raw: str, prefix: str) -> str:
    tail = raw.strip().lower().replace(" ", "_")
    tail = _UNSAFE.sub("_", tail)
    tail = _REPEATS.sub("_", tail).strip("_")
    if not tail:
        raise NamingError("Название должно содержать латинские буквы или цифры")
    if tail.startswith(prefix):
        return tail
    return f"{prefix}{tail}"
