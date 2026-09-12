package terminal

import (
	"log"
	"os"
	"path/filepath"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// CodexAdapter sets `[tui].theme` in ~/.codex/config.toml (OpenAI Codex
// CLI). Codex's 32 bundled themes are TextMate-derived kebab-case slugs
// (e.g. "gruvbox-dark") without a documented complete catalog, so — like
// Yazi — there's no safe universal default to guess; this is opt-in via
// codex_light_theme / codex_dark_theme. Only patches an existing
// config.toml; never creates one, since Codex's config carries many
// required-looking settings this adapter has no business inventing.
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
