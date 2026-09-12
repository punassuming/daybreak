package terminal

import (
	"log"
	"os"
	"path/filepath"

	"github.com/tidwall/gjson"
	"github.com/tidwall/sjson"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// ClaudeCodeAdapter sets the "theme" key in ~/.claude/settings.json.
// Claude Code documents "light"/"dark" (plus daltonized/ansi variants) as
// always-available built-in presets, so unlike Yazi/Codex these have safe
// non-empty defaults. Only touches the file if it already exists — a
// missing ~/.claude means Claude Code was never installed here.
//
// Uses sjson for a surgical in-place set rather than this package's
// LoadJSONCFile/DumpJSONFile (which round-trips through a Go map and, on
// write, both re-sorts keys alphabetically and reformats indentation —
// acceptable for Windows Terminal/Obsidian's settings, but needlessly
// noisy for a hand-maintained settings.json most users track in dotfiles).
type ClaudeCodeAdapter struct {
	Config *config.Manager
}

func (ClaudeCodeAdapter) Name() string { return "claude_code" }

func (a ClaudeCodeAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	path := claudeCodeSettingsPath()
	if path == "" {
		return nil
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil
	}

	def := "dark"
	if mode == "light" {
		def = "light"
	}
	targetTheme := a.Config.GetIntegration("claude_code_"+mode+"_theme", def)

	if gjson.GetBytes(raw, "theme").String() == targetTheme {
		return nil
	}

	updated, err := sjson.SetBytes(raw, "theme", targetTheme)
	if err != nil {
		log.Printf("Claude Code: failed to update %s: %v", path, err)
		return nil
	}

	if err := os.WriteFile(path, updated, 0o644); err != nil {
		log.Printf("Claude Code: failed writing %s: %v", path, err)
		return nil
	}
	log.Printf("Claude Code: applied theme '%s' to %s", targetTheme, path)
	return nil
}

func claudeCodeSettingsPath() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".claude", "settings.json")
}
