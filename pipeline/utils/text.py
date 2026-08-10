import re


def normalize_plaza_name(name: str | None) -> str | None:
    """
    Normalizes a toll location name for matching invoice.toll_loc_name_start
    against the SDK response's toll name field.
    """
    if not name:
        return None
    normalized = name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized or None