package theme

import (
	"sort"
	"strings"
)

// Registry mirrors core/theme_registry.py's ThemeRegistry.
type Registry struct{}

// NewRegistry constructs a Registry (stateless, kept for parity with the
// Python class-based API and to leave room for future caching).
func NewRegistry() *Registry { return &Registry{} }

// ListThemes mirrors ThemeRegistry.list_themes.
func (r *Registry) ListThemes() []string {
	names := ListThemeNames()
	sort.Strings(names)
	return names
}

// GetPalette mirrors ThemeRegistry.get_palette.
func (r *Registry) GetPalette(themeName, mode string) (Palette, error) {
	normalizedMode, err := NormalizeMode(mode)
	if err != nil {
		return Palette{}, err
	}
	set := GetThemePalette(themeName)
	if normalizedMode == "light" {
		return set.Light, nil
	}
	return set.Dark, nil
}

// GetTokens mirrors ThemeRegistry.get_tokens.
func (r *Registry) GetTokens(themeName, mode string) (map[string]string, error) {
	palette, err := r.GetPalette(themeName, mode)
	if err != nil {
		return nil, err
	}
	tokens := PaletteToTokens(palette, mode)
	if err := ValidateTokens(tokens); err != nil {
		return nil, err
	}
	return tokens, nil
}

// GetAccentTokens mirrors ThemeRegistry.get_accent_tokens.
func (r *Registry) GetAccentTokens(themeName, mode string) (map[string]string, error) {
	palette, err := r.GetPalette(themeName, mode)
	if err != nil {
		return nil, err
	}
	return PaletteToAccentTokens(palette, mode), nil
}

// Theme is the full descriptor returned by GetTheme, mirroring
// ThemeRegistry.get_theme's dict shape.
type Theme struct {
	ID           string
	Name         string
	Mode         string
	Tokens       map[string]string
	AccentTokens map[string]string
	Palette      Palette
}

// GetTheme mirrors ThemeRegistry.get_theme.
func (r *Registry) GetTheme(themeName, mode string) (Theme, error) {
	normalizedMode, err := NormalizeMode(mode)
	if err != nil {
		return Theme{}, err
	}
	tokens, err := r.GetTokens(themeName, normalizedMode)
	if err != nil {
		return Theme{}, err
	}
	accentTokens, err := r.GetAccentTokens(themeName, normalizedMode)
	if err != nil {
		return Theme{}, err
	}
	palette, err := r.GetPalette(themeName, normalizedMode)
	if err != nil {
		return Theme{}, err
	}
	id := strings.ReplaceAll(strings.ToLower(themeName), " ", "-")
	return Theme{
		ID:           id,
		Name:         themeName,
		Mode:         normalizedMode,
		Tokens:       tokens,
		AccentTokens: accentTokens,
		Palette:      palette,
	}, nil
}
