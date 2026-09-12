package theme

// PaletteToTokens mirrors theme_transform.palette_to_tokens.
func PaletteToTokens(palette Palette, mode string) map[string]string {
	special := palette.Special
	colors := palette.Colors

	defaultBg := "#f5f5f5"
	defaultFg := "#121212"
	if mode == "dark" {
		defaultBg = "#111111"
		defaultFg = "#e5e5e5"
	}

	bg := fallback(special["background"], defaultBg)
	fg := fallback(special["foreground"], defaultFg)
	cursor := fallback(special["cursor"], fg)

	muted := fallback(colors["8"], fg)
	primary := fallback(colors["4"], fg)
	success := fallback(colors["2"], fg)
	warning := fallback(colors["3"], fg)
	errorColor := fallback(colors["1"], fg)
	info := fallback(colors["6"], primary)

	surface1 := fallback(colors["18"], bg)
	surface2 := fallback(colors["19"], surface1)
	surface3 := fallback(colors["20"], muted)

	tokens := map[string]string{
		"bg":        bg,
		"fg":        fg,
		"cursor":    cursor,
		"muted":     muted,
		"primary":   primary,
		"success":   success,
		"warning":   warning,
		"error":     errorColor,
		"info":      info,
		"surface_1": surface1,
		"surface_2": surface2,
		"surface_3": surface3,
	}

	for _, key := range []string{"fg", "muted", "primary", "success", "warning", "error", "info"} {
		tokens[key] = AdjustColorForContrast(tokens[key], bg, 4.0)
	}

	return tokens
}

// PaletteToAccentTokens mirrors theme_transform.palette_to_accent_tokens.
func PaletteToAccentTokens(palette Palette, mode string) map[string]string {
	special := palette.Special
	colors := palette.Colors

	defaultBg := "#f5f5f5"
	if mode == "dark" {
		defaultBg = "#111111"
	}
	bg := fallback(special["background"], defaultBg)

	accentPrimary := fallback(colors["4"], fallback(special["foreground"], bg))
	accentSecondary := fallback(colors["5"], accentPrimary)
	accentSuccess := fallback(colors["2"], fallback(special["foreground"], bg))
	accentWarning := fallback(colors["3"], accentPrimary)
	accentError := fallback(colors["1"], accentPrimary)
	accentSelection := fallback(colors["18"], bg)

	accents := map[string]string{
		"accent_primary":   accentPrimary,
		"accent_secondary": accentSecondary,
		"accent_success":   accentSuccess,
		"accent_warning":   accentWarning,
		"accent_error":     accentError,
		"accent_selection": accentSelection,
	}

	for _, key := range []string{"accent_primary", "accent_secondary", "accent_success", "accent_warning", "accent_error"} {
		accents[key] = AdjustColorForContrast(accents[key], bg, 3.0)
	}

	return accents
}
