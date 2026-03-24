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


def palette_to_accent_tokens(palette: dict, mode: str) -> dict:
    """Derive semantic accent tokens from a palette using contrast-safe utilities."""
    special = palette.get("special", {})
    colors = palette.get("colors", {})

    bg = _fallback(special.get("background"), "#111111" if mode == "dark" else "#f5f5f5")

    accent_primary = _fallback(colors.get("4"), _fallback(special.get("foreground"), bg))
    accent_secondary = _fallback(colors.get("5"), accent_primary)
    accent_success = _fallback(colors.get("2"), _fallback(special.get("foreground"), bg))
    accent_warning = _fallback(colors.get("3"), accent_primary)
    accent_error = _fallback(colors.get("1"), accent_primary)
    accent_selection = _fallback(colors.get("18"), bg)

    accents = {
        "accent_primary": accent_primary,
        "accent_secondary": accent_secondary,
        "accent_success": accent_success,
        "accent_warning": accent_warning,
        "accent_error": accent_error,
        "accent_selection": accent_selection,
    }

    # Ensure foreground accent colors meet a minimum contrast against background.
    for key in ("accent_primary", "accent_secondary", "accent_success", "accent_warning", "accent_error"):
        accents[key] = adjust_color_for_contrast(accents[key], bg, min_ratio=3.0)

    return accents
