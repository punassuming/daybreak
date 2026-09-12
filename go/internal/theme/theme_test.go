package theme

import (
	"regexp"
	"testing"
)

var hexRE = regexp.MustCompile(`^#[0-9a-f]{6}$`)

func TestAccentKeysDefined(t *testing.T) {
	expected := map[string]bool{
		"accent_primary": true, "accent_secondary": true, "accent_success": true,
		"accent_warning": true, "accent_error": true, "accent_selection": true,
	}
	if len(AccentKeys) != len(expected) {
		t.Fatalf("AccentKeys length = %d, want %d", len(AccentKeys), len(expected))
	}
	for _, k := range AccentKeys {
		if !expected[k] {
			t.Errorf("unexpected accent key %q", k)
		}
	}
}

var darkTestPalette = Palette{
	Special: map[string]string{"background": "#2e3440", "foreground": "#d8dee9", "cursor": "#d8dee9"},
	Colors: map[string]string{
		"1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
		"4": "#81a1c1", "5": "#b48ead",
	},
}

func TestAllAccentKeysPresent(t *testing.T) {
	accents := PaletteToAccentTokens(darkTestPalette, "dark")
	for _, key := range AccentKeys {
		if _, ok := accents[key]; !ok {
			t.Errorf("missing accent key: %s", key)
		}
	}
}

func TestAccentValuesAreHexColors(t *testing.T) {
	accents := PaletteToAccentTokens(darkTestPalette, "dark")
	for key, value := range accents {
		if !hexRE.MatchString(value) {
			t.Errorf("invalid hex for %s: %s", key, value)
		}
	}
}

func TestAccentTokensLightMode(t *testing.T) {
	lightPalette := Palette{
		Special: map[string]string{"background": "#e5e9f0", "foreground": "#2e3440", "cursor": "#2e3440"},
		Colors: map[string]string{
			"1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
			"4": "#5e81ac", "5": "#b48ead",
		},
	}
	accents := PaletteToAccentTokens(lightPalette, "light")
	for _, key := range AccentKeys {
		if _, ok := accents[key]; !ok {
			t.Errorf("missing accent key: %s", key)
		}
	}
	if !hexRE.MatchString(accents["accent_primary"]) {
		t.Errorf("invalid hex for accent_primary: %s", accents["accent_primary"])
	}
}

func TestAccentTokensEmptyPaletteDoesNotCrash(t *testing.T) {
	accents := PaletteToAccentTokens(Palette{}, "dark")
	for _, key := range AccentKeys {
		if _, ok := accents[key]; !ok {
			t.Errorf("missing accent key: %s", key)
		}
	}
}

func TestRegistryListThemesContainsNord(t *testing.T) {
	r := NewRegistry()
	found := false
	for _, name := range r.ListThemes() {
		if name == "Nord" {
			found = true
		}
	}
	if !found {
		t.Error("expected 'Nord' in ListThemes()")
	}
}

func TestRegistryTokensHaveRequiredSemanticKeys(t *testing.T) {
	r := NewRegistry()
	tokens, err := r.GetTokens("Nord", "dark")
	if err != nil {
		t.Fatal(err)
	}
	for _, key := range TokenKeys {
		v, ok := tokens[key]
		if !ok {
			t.Errorf("missing token key: %s", key)
			continue
		}
		if !hexRE.MatchString(v) {
			t.Errorf("invalid hex for %s: %s", key, v)
		}
	}
}

func TestRegistryGetAccentTokensReturnsAllKeys(t *testing.T) {
	r := NewRegistry()
	accents, err := r.GetAccentTokens("Nord", "dark")
	if err != nil {
		t.Fatal(err)
	}
	for _, key := range AccentKeys {
		if _, ok := accents[key]; !ok {
			t.Errorf("missing accent key: %s", key)
		}
	}
}

func TestRegistryGetAccentTokensHexFormat(t *testing.T) {
	r := NewRegistry()
	accents, err := r.GetAccentTokens("Gruvbox", "light")
	if err != nil {
		t.Fatal(err)
	}
	for key, value := range accents {
		if !hexRE.MatchString(value) {
			t.Errorf("invalid hex for %s: %s", key, value)
		}
	}
}

func TestRegistryGetThemeIncludesAccentTokens(t *testing.T) {
	r := NewRegistry()
	th, err := r.GetTheme("Nord", "dark")
	if err != nil {
		t.Fatal(err)
	}
	for _, key := range AccentKeys {
		if _, ok := th.AccentTokens[key]; !ok {
			t.Errorf("theme.AccentTokens missing %s", key)
		}
	}
}

func TestRegistryAccentTokensAllThemes(t *testing.T) {
	r := NewRegistry()
	for _, themeName := range r.ListThemes() {
		for _, mode := range []string{"light", "dark"} {
			accents, err := r.GetAccentTokens(themeName, mode)
			if err != nil {
				t.Fatalf("%s/%s: %v", themeName, mode, err)
			}
			for _, key := range AccentKeys {
				v, ok := accents[key]
				if !ok {
					t.Errorf("%s/%s missing %s", themeName, mode, key)
					continue
				}
				if !hexRE.MatchString(v) {
					t.Errorf("%s/%s/%s not valid hex: %s", themeName, mode, key, v)
				}
			}
		}
	}
}
