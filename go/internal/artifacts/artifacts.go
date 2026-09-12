// Package artifacts ports core/artifacts.py: writes Daybreak-owned shared
// theme state (palette.json, env.sh, ls_colors.sh) into the config
// directory after every mode switch. All writes are best-effort — callers
// should treat failures as non-fatal, matching the Python contract.
package artifacts

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"

	"daybreak/internal/theme"
)

// Generate mirrors artifacts.generate_artifacts.
func Generate(configDir, themeName, mode string, tokens, accentTokens map[string]string, palette theme.Palette) {
	if err := os.MkdirAll(configDir, 0o755); err != nil {
		log.Printf("Failed to write theme artifacts: %v", err)
		return
	}
	if err := writePaletteJSON(configDir, themeName, mode, tokens, accentTokens, palette); err != nil {
		log.Printf("Failed to write theme artifacts: %v", err)
		return
	}
	if err := writeEnvSh(configDir, themeName, mode, tokens, accentTokens); err != nil {
		log.Printf("Failed to write theme artifacts: %v", err)
		return
	}
	if err := writeLSColors(configDir, mode, tokens); err != nil {
		log.Printf("Failed to write theme artifacts: %v", err)
		return
	}
}

type paletteArtifact struct {
	Theme        string            `json:"theme"`
	Mode         string            `json:"mode"`
	Tokens       map[string]string `json:"tokens"`
	AccentTokens map[string]string `json:"accent_tokens"`
	Palette      struct {
		Special map[string]string `json:"special"`
		Colors  map[string]string `json:"colors"`
	} `json:"palette"`
}

func writePaletteJSON(configDir, themeName, mode string, tokens, accentTokens map[string]string, palette theme.Palette) error {
	data := paletteArtifact{
		Theme:        themeName,
		Mode:         mode,
		Tokens:       tokens,
		AccentTokens: accentTokens,
	}
	data.Palette.Special = palette.Special
	data.Palette.Colors = palette.Colors

	out, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(filepath.Join(configDir, "palette.json"), out, 0o644)
}

func writeEnvSh(configDir, themeName, mode string, tokens, accentTokens map[string]string) error {
	lines := []string{
		"# Daybreak theme environment — auto-generated, do not edit manually",
		fmt.Sprintf(`DAYBREAK_THEME="%s"`, themeName),
		fmt.Sprintf(`DAYBREAK_MODE="%s"`, mode),
		fmt.Sprintf(`DAYBREAK_COLOR_BG="%s"`, tokens["bg"]),
		fmt.Sprintf(`DAYBREAK_COLOR_FG="%s"`, tokens["fg"]),
		fmt.Sprintf(`DAYBREAK_COLOR_PRIMARY="%s"`, tokens["primary"]),
		fmt.Sprintf(`DAYBREAK_COLOR_SUCCESS="%s"`, tokens["success"]),
		fmt.Sprintf(`DAYBREAK_COLOR_WARNING="%s"`, tokens["warning"]),
		fmt.Sprintf(`DAYBREAK_COLOR_ERROR="%s"`, tokens["error"]),
		fmt.Sprintf(`DAYBREAK_COLOR_INFO="%s"`, tokens["info"]),
		fmt.Sprintf(`DAYBREAK_ACCENT_PRIMARY="%s"`, accentTokens["accent_primary"]),
		fmt.Sprintf(`DAYBREAK_ACCENT_SECONDARY="%s"`, accentTokens["accent_secondary"]),
		fmt.Sprintf(`DAYBREAK_ACCENT_SUCCESS="%s"`, accentTokens["accent_success"]),
		fmt.Sprintf(`DAYBREAK_ACCENT_WARNING="%s"`, accentTokens["accent_warning"]),
		fmt.Sprintf(`DAYBREAK_ACCENT_ERROR="%s"`, accentTokens["accent_error"]),
		fmt.Sprintf(`DAYBREAK_ACCENT_SELECTION="%s"`, accentTokens["accent_selection"]),
		"export DAYBREAK_THEME DAYBREAK_MODE",
		"export DAYBREAK_COLOR_BG DAYBREAK_COLOR_FG DAYBREAK_COLOR_PRIMARY",
		"export DAYBREAK_COLOR_SUCCESS DAYBREAK_COLOR_WARNING DAYBREAK_COLOR_ERROR DAYBREAK_COLOR_INFO",
		"export DAYBREAK_ACCENT_PRIMARY DAYBREAK_ACCENT_SECONDARY DAYBREAK_ACCENT_SUCCESS",
		"export DAYBREAK_ACCENT_WARNING DAYBREAK_ACCENT_ERROR DAYBREAK_ACCENT_SELECTION",
	}
	return writeLines(filepath.Join(configDir, "env.sh"), lines)
}

func writeLSColors(configDir, mode string, tokens map[string]string) error {
	fg := func(hexColor string) string {
		r, g, b := theme.HexToRGB(hexColor)
		return fmt.Sprintf("38;2;%d;%d;%d", r, g, b)
	}

	type entry struct {
		key   string
		value string
	}
	entries := []entry{
		{"di", fmt.Sprintf("1;%s", fg(tokens["primary"]))},
		{"ln", fg(tokens["info"])},
		{"ex", fg(tokens["success"])},
		{"pi", fg(tokens["warning"])},
		{"so", fg(tokens["info"])},
		{"bd", fg(tokens["warning"])},
		{"cd", fg(tokens["warning"])},
		{"or", fg(tokens["error"])},
		{"mi", fg(tokens["error"])},
		{"*.tar", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.tgz", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.gz", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.bz2", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.xz", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.zip", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.7z", fmt.Sprintf("1;%s", fg(tokens["error"]))},
		{"*.py", fg(tokens["primary"])},
		{"*.sh", fg(tokens["success"])},
		{"*.bash", fg(tokens["success"])},
		{"*.zsh", fg(tokens["success"])},
		{"*.fish", fg(tokens["success"])},
		{"*.json", fg(tokens["warning"])},
		{"*.toml", fg(tokens["warning"])},
		{"*.yaml", fg(tokens["warning"])},
		{"*.yml", fg(tokens["warning"])},
		{"*.ini", fg(tokens["warning"])},
		{"*.cfg", fg(tokens["warning"])},
		{"*.md", fg(tokens["info"])},
		{"*.rst", fg(tokens["info"])},
		{"*.txt", fg(tokens["muted"])},
	}

	lsColorsParts := make([]string, 0, len(entries))
	for _, e := range entries {
		lsColorsParts = append(lsColorsParts, fmt.Sprintf("%s=%s", e.key, e.value))
	}
	lsColorsValue := ""
	for i, p := range lsColorsParts {
		if i > 0 {
			lsColorsValue += ":"
		}
		lsColorsValue += p
	}

	lines := []string{
		"# Daybreak LS_COLORS — auto-generated, do not edit manually",
		"# Source this file to apply terminal file-type colours:",
		`#   [ -f "$HOME/.config/daybreak/ls_colors.sh" ] && . "$HOME/.config/daybreak/ls_colors.sh"`,
		fmt.Sprintf(`LS_COLORS="%s"`, lsColorsValue),
		"export LS_COLORS",
	}
	return writeLines(filepath.Join(configDir, "ls_colors.sh"), lines)
}

func writeLines(path string, lines []string) error {
	content := ""
	for _, l := range lines {
		content += l + "\n"
	}
	return os.WriteFile(path, []byte(content), 0o644)
}
