from typing import Dict

THEME_MODES = {"light", "dark"}

TOKEN_KEYS = (
    "bg",
    "fg",
    "cursor",
    "muted",
    "primary",
    "success",
    "warning",
    "error",
    "info",
    "surface_1",
    "surface_2",
    "surface_3",
)


def normalize_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized not in THEME_MODES:
        raise ValueError(f"Unsupported mode '{mode}'. Expected one of: {sorted(THEME_MODES)}")
    return normalized


def is_hex_color(value: str) -> bool:
    if not isinstance(value, str):
        return False
    if len(value) != 7 or not value.startswith("#"):
        return False
    try:
        int(value[1:], 16)
    except ValueError:
        return False
    return True


def validate_tokens(tokens: Dict[str, str]) -> None:
    missing = [key for key in TOKEN_KEYS if key not in tokens]
    if missing:
        raise ValueError(f"Theme tokens missing required keys: {missing}")

    invalid = [key for key, value in tokens.items() if key in TOKEN_KEYS and not is_hex_color(value)]
    if invalid:
        raise ValueError(f"Theme tokens contain invalid hex colors for keys: {invalid}")
