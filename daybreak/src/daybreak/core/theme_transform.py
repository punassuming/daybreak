from daybreak.colors import adjust_color_for_contrast


def _fallback(value, default):
    return value if value else default


def palette_to_tokens(palette: dict, mode: str) -> dict:
    special = palette.get("special", {})
    colors = palette.get("colors", {})

    bg = _fallback(special.get("background"), "#111111" if mode == "dark" else "#f5f5f5")
    fg = _fallback(special.get("foreground"), "#e5e5e5" if mode == "dark" else "#121212")
    cursor = _fallback(special.get("cursor"), fg)

    muted = _fallback(colors.get("8"), fg)
    primary = _fallback(colors.get("4"), fg)
    success = _fallback(colors.get("2"), fg)
    warning = _fallback(colors.get("3"), fg)
    error = _fallback(colors.get("1"), fg)
    info = _fallback(colors.get("6"), primary)

    surface_1 = _fallback(colors.get("18"), bg)
    surface_2 = _fallback(colors.get("19"), surface_1)
    surface_3 = _fallback(colors.get("20"), muted)

    tokens = {
        "bg": bg,
        "fg": fg,
        "cursor": cursor,
        "muted": muted,
        "primary": primary,
        "success": success,
        "warning": warning,
        "error": error,
        "info": info,
        "surface_1": surface_1,
        "surface_2": surface_2,
        "surface_3": surface_3,
    }

    # Keep semantic foreground tokens readable against the main surface.
    for key in ("fg", "muted", "primary", "success", "warning", "error", "info"):
        tokens[key] = adjust_color_for_contrast(tokens[key], bg, min_ratio=4.0)

    return tokens
