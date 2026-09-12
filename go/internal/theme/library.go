package theme

import "math"

// themeDef holds a theme's base dark/light palettes; a zero-value Colors map
// (nil) means "not provided, generate the other mode from it".
type themeDef struct {
	Dark  Palette
	Light Palette
}

func special(bg, fg, cursor string) map[string]string {
	return map[string]string{"background": bg, "foreground": fg, "cursor": cursor}
}

var themeLibrary = map[string]themeDef{
	"Nord": {
		Dark: Palette{
			Special: special("#2e3440", "#d8dee9", "#d8dee9"),
			Colors: map[string]string{
				"0": "#3b4252", "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
				"4": "#81a1c1", "5": "#b48ead", "6": "#88c0d0", "7": "#e5e9f0",
				"8": "#4c566a", "9": "#bf616a", "10": "#a3be8c", "11": "#ebcb8b",
				"12": "#81a1c1", "13": "#b48ead", "14": "#8fbcbb", "15": "#eceff4",
			},
		},
		Light: Palette{
			Special: special("#e5e9f0", "#2e3440", "#2e3440"),
			Colors: map[string]string{
				"0": "#d8dee9", "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
				"4": "#5e81ac", "5": "#b48ead", "6": "#88c0d0", "7": "#3b4252",
				"8": "#4c566a", "9": "#bf616a", "10": "#a3be8c", "11": "#ebcb8b",
				"12": "#5e81ac", "13": "#b48ead", "14": "#8fbcbb", "15": "#2e3440",
			},
		},
	},
	"Gruvbox": {
		Dark: Palette{
			Special: special("#282828", "#ebdbb2", "#ebdbb2"),
			Colors: map[string]string{
				"0": "#282828", "1": "#cc241d", "2": "#98971a", "3": "#d79921",
				"4": "#458588", "5": "#b16286", "6": "#689d6a", "7": "#a89984",
				"8": "#928374", "9": "#fb4934", "10": "#b8bb26", "11": "#fabd2f",
				"12": "#83a598", "13": "#d3869b", "14": "#8ec07c", "15": "#ebdbb2",
			},
		},
		Light: Palette{
			Special: special("#fbf1c7", "#3c3836", "#3c3836"),
			Colors: map[string]string{
				"0": "#fbf1c7", "1": "#cc241d", "2": "#98971a", "3": "#d79921",
				"4": "#458588", "5": "#b16286", "6": "#689d6a", "7": "#7c6f64",
				"8": "#928374", "9": "#9d0006", "10": "#79740e", "11": "#b57614",
				"12": "#076678", "13": "#8f3f71", "14": "#427b58", "15": "#3c3836",
			},
		},
	},
	"Dracula": {
		Dark: Palette{
			Special: special("#282a36", "#f8f8f2", "#f8f8f2"),
			Colors: map[string]string{
				"0": "#21222c", "1": "#ff5555", "2": "#50fa7b", "3": "#f1fa8c",
				"4": "#bd93f9", "5": "#ff79c6", "6": "#8be9fd", "7": "#f8f8f2",
				"8": "#6272a4", "9": "#ff6e6e", "10": "#69ff94", "11": "#ffffa5",
				"12": "#d6acff", "13": "#ff92df", "14": "#a4ffff", "15": "#ffffff",
			},
		},
		// Light intentionally omitted: auto-generated from dark.
	},
	"Solarized": {
		Dark: Palette{
			Special: special("#002b36", "#839496", "#839496"),
			Colors: map[string]string{
				"0": "#073642", "1": "#dc322f", "2": "#859900", "3": "#b58900",
				"4": "#268bd2", "5": "#d33682", "6": "#2aa198", "7": "#eee8d5",
				"8": "#002b36", "9": "#cb4b16", "10": "#586e75", "11": "#657b83",
				"12": "#839496", "13": "#6c71c4", "14": "#93a1a1", "15": "#fdf6e3",
			},
		},
		Light: Palette{
			Special: special("#fdf6e3", "#657b83", "#657b83"),
			Colors: map[string]string{
				"0": "#eee8d5", "1": "#dc322f", "2": "#859900", "3": "#b58900",
				"4": "#268bd2", "5": "#d33682", "6": "#2aa198", "7": "#073642",
				"8": "#fdf6e3", "9": "#cb4b16", "10": "#586e75", "11": "#657b83",
				"12": "#839496", "13": "#6c71c4", "14": "#93a1a1", "15": "#002b36",
			},
		},
	},
	"Catppuccin": {
		Dark: Palette{
			Special: special("#1e1e2e", "#cdd6f4", "#cdd6f4"),
			Colors: map[string]string{
				"0": "#45475a", "1": "#f38ba8", "2": "#a6e3a1", "3": "#f9e2af",
				"4": "#89b4fa", "5": "#f5c2e7", "6": "#94e2d5", "7": "#bac2de",
				"8": "#585b70", "9": "#f38ba8", "10": "#a6e3a1", "11": "#f9e2af",
				"12": "#89b4fa", "13": "#f5c2e7", "14": "#94e2d5", "15": "#a6adc8",
			},
		},
		Light: Palette{
			Special: special("#eff1f5", "#4c4f69", "#4c4f69"),
			Colors: map[string]string{
				"0": "#5c5f77", "1": "#d20f39", "2": "#40a02b", "3": "#df8e1d",
				"4": "#1e66f5", "5": "#ea76cb", "6": "#179299", "7": "#acb0be",
				"8": "#6c6f85", "9": "#d20f39", "10": "#40a02b", "11": "#df8e1d",
				"12": "#1e66f5", "13": "#ea76cb", "14": "#179299", "15": "#ffffff",
			},
		},
	},
	"Tokyo Night": {
		Dark: Palette{
			Special: special("#1a1b26", "#c0caf5", "#c0caf5"),
			Colors: map[string]string{
				"0": "#15161e", "1": "#f7768e", "2": "#9ece6a", "3": "#e0af68",
				"4": "#7aa2f7", "5": "#bb9af7", "6": "#7dcfff", "7": "#a9b1d6",
				"8": "#414868", "9": "#f7768e", "10": "#9ece6a", "11": "#e0af68",
				"12": "#7aa2f7", "13": "#bb9af7", "14": "#7dcfff", "15": "#c0caf5",
			},
		},
		Light: Palette{
			Special: special("#e1e2e7", "#3760bf", "#3760bf"),
			Colors: map[string]string{
				"0": "#d5d6db", "1": "#f52a65", "2": "#587539", "3": "#8c6c3e",
				"4": "#2e5cb8", "5": "#9854f1", "6": "#007197", "7": "#6172b0",
				"8": "#a1a6b2", "9": "#f52a65", "10": "#587539", "11": "#8c6c3e",
				"12": "#2e5cb8", "13": "#9854f1", "14": "#007197", "15": "#ffffff",
			},
		},
	},
	"Monokai": {
		Dark: Palette{
			Special: special("#272822", "#f8f8f2", "#f8f8f2"),
			Colors: map[string]string{
				"0": "#272822", "1": "#f92672", "2": "#a6e22e", "3": "#f4bf75",
				"4": "#66d9ef", "5": "#ae81ff", "6": "#a1efe4", "7": "#f8f8f2",
				"8": "#75715e", "9": "#f92672", "10": "#a6e22e", "11": "#f4bf75",
				"12": "#66d9ef", "13": "#ae81ff", "14": "#a1efe4", "15": "#f9f8f5",
			},
		},
	},
	"One Dark": {
		Dark: Palette{
			Special: special("#282c34", "#abb2bf", "#abb2bf"),
			Colors: map[string]string{
				"0": "#282c34", "1": "#e06c75", "2": "#98c379", "3": "#e5c07b",
				"4": "#61afef", "5": "#c678dd", "6": "#56b6c2", "7": "#abb2bf",
				"8": "#5c6370", "9": "#e06c75", "10": "#98c379", "11": "#e5c07b",
				"12": "#61afef", "13": "#c678dd", "14": "#56b6c2", "15": "#ffffff",
			},
		},
	},
}

// ListThemeNames mirrors THEME_LIBRARY.keys() surfaced for the CLI/registry.
func ListThemeNames() []string {
	names := make([]string, 0, len(themeLibrary))
	for name := range themeLibrary {
		names = append(names, name)
	}
	return names
}

// ThemeModeSet holds the (possibly generated) light+dark palettes for a theme.
type ThemeModeSet struct {
	Light Palette
	Dark  Palette
}

func hasColors(p Palette) bool { return p.Colors != nil }

// GetThemePalette mirrors themes.get_theme_palette: returns light+dark,
// generating whichever mode is missing, then enriching both to depth 21.
// Falls back to Nord for unknown theme names, matching the Python fallback.
func GetThemePalette(themeName string) ThemeModeSet {
	def, ok := themeLibrary[themeName]
	if !ok {
		def = themeLibrary["Nord"]
	}

	result := ThemeModeSet{Light: def.Light, Dark: def.Dark}

	if !hasColors(result.Light) && hasColors(result.Dark) {
		result.Light = GenerateLightFromDark(result.Dark)
		result.Light.Generated = true
	}
	if !hasColors(result.Dark) && hasColors(result.Light) {
		result.Dark = GenerateDarkFromLight(result.Light)
		result.Dark.Generated = true
	}

	enrichPaletteDepth(&result.Light, "light")
	enrichPaletteDepth(&result.Dark, "dark")

	return result
}

// enrichPaletteDepth mirrors themes._enrich_palette_depth: adds extended
// indices 16/18/19/20/21 for richer UI elements when not already present.
func enrichPaletteDepth(palette *Palette, mode string) {
	if palette.Colors == nil {
		palette.Colors = map[string]string{}
	}

	bg := palette.Special["background"]
	fg := palette.Special["foreground"]

	adjustBg := func(hexC string, amount float64) string {
		r, g, b := HexToRGB(hexC)
		h, l, s := rgbToHLS(float64(r)/255.0, float64(g)/255.0, float64(b)/255.0)
		if mode == "dark" {
			l = math.Min(1.0, l+amount)
		} else {
			l = math.Max(0.0, l-amount)
		}
		rr, rg, rb := hlsToRGB(h, l, s)
		return RGBToHex(rr*255, rg*255, rb*255)
	}

	if _, ok := palette.Colors["18"]; !ok {
		palette.Colors["18"] = adjustBg(bg, 0.10)
	}
	if _, ok := palette.Colors["19"]; !ok {
		palette.Colors["19"] = adjustBg(bg, 0.20)
	}
	if _, ok := palette.Colors["16"]; !ok {
		if v, has11 := palette.Colors["11"]; has11 {
			palette.Colors["16"] = v
		}
	}
	if _, ok := palette.Colors["20"]; !ok {
		palette.Colors["20"] = palette.Colors["8"]
	}
	if _, ok := palette.Colors["21"]; !ok {
		palette.Colors["21"] = fg
	}
}
