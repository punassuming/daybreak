package theme

import (
	"fmt"
	"sort"
	"strconv"
	"strings"
)

// TokenKeys mirrors theme_model.TOKEN_KEYS.
var TokenKeys = []string{
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
}

// AccentKeys mirrors theme_model.ACCENT_KEYS.
var AccentKeys = []string{
	"accent_primary",
	"accent_secondary",
	"accent_success",
	"accent_warning",
	"accent_error",
	"accent_selection",
}

var themeModes = map[string]bool{"light": true, "dark": true}

// NormalizeMode mirrors normalize_mode: lowercases/trims and rejects
// anything other than "light"/"dark".
func NormalizeMode(mode string) (string, error) {
	normalized := strings.ToLower(strings.TrimSpace(mode))
	if !themeModes[normalized] {
		modes := make([]string, 0, len(themeModes))
		for m := range themeModes {
			modes = append(modes, m)
		}
		sort.Strings(modes)
		return "", fmt.Errorf("unsupported mode '%s'. Expected one of: %v", mode, modes)
	}
	return normalized, nil
}

// IsHexColor mirrors is_hex_color.
func IsHexColor(value string) bool {
	if len(value) != 7 || value[0] != '#' {
		return false
	}
	_, err := strconv.ParseInt(value[1:], 16, 32)
	return err == nil
}

// ValidateTokens mirrors validate_tokens.
func ValidateTokens(tokens map[string]string) error {
	var missing []string
	for _, key := range TokenKeys {
		if _, ok := tokens[key]; !ok {
			missing = append(missing, key)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("theme tokens missing required keys: %v", missing)
	}

	var invalid []string
	for _, key := range TokenKeys {
		if !IsHexColor(tokens[key]) {
			invalid = append(invalid, key)
		}
	}
	if len(invalid) > 0 {
		return fmt.Errorf("theme tokens contain invalid hex colors for keys: %v", invalid)
	}
	return nil
}
