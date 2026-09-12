package theme

// Palette mirrors the Python palette dict shape: {"special": {...}, "colors": {...}}.
// Colors are keyed by ANSI index as a string ("0".."21") to match theme.py.
type Palette struct {
	Special   map[string]string
	Colors    map[string]string
	Generated bool
}

func clonePalette(p Palette) Palette {
	special := make(map[string]string, len(p.Special))
	for k, v := range p.Special {
		special[k] = v
	}
	colors := make(map[string]string, len(p.Colors))
	for k, v := range p.Colors {
		colors[k] = v
	}
	return Palette{Special: special, Colors: colors, Generated: p.Generated}
}

func fallback(value, def string) string {
	if value != "" {
		return value
	}
	return def
}
