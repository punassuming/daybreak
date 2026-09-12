package terminal

import (
	"log"
	"os"
	"path/filepath"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// CodexAdapter sets `[tui].theme` in ~/.codex/config.toml (OpenAI Codex
// CLI). Codex's 32 bundled themes are TextMate-derived kebab-case slugs;
// "one-half-light"/"one-half-dark" (matching the Windows Terminal
// defaults) were confirmed valid live via Codex's own /theme picker.
// Still overridable via codex_light_theme / codex_dark_theme for anyone
// who prefers a different bundled theme. Only patches an existing
// config.toml; never creates one, since Codex's config carries many
// required-looking settings this adapter has no business inventing.
//
// Note: `tui.theme` controls Codex's syntax-highlighting palette. If the
// terminal input box itself still looks wrong after this applies, that
// background likely comes from the enclosing terminal, not from Codex.
type CodexAdapter struct {
	Config *config.Manager
}

func (CodexAdapter) Name() string { return "codex" }

func (a CodexAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	targetTheme := a.Config.GetIntegration("codex_"+mode+"_theme", "")
	if targetTheme == "" {
		return nil
	}

	path := codexConfigPath()
	if path == "" {
		return nil
	}
	if _, err := os.Stat(path); err != nil {
		return nil
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		log.Printf("Codex: failed to read %s: %v", path, err)
		return nil
	}

	updated := upsertTOMLKey(string(raw), "tui", "theme", targetTheme)
	if updated == string(raw) {
		return nil
	}
	if err := os.WriteFile(path, []byte(updated), 0o644); err != nil {
		log.Printf("Codex: failed to update %s: %v", path, err)
		return nil
	}
	log.Printf("Codex: applied theme '%s' to %s", targetTheme, path)
	return nil
}

func codexConfigPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".codex", "config.toml")
}
