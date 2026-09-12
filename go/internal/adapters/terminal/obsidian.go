//go:build windows

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

// ObsidianAdapter sets the "theme" key in Obsidian's global settings file
// (~%APPDATA%\obsidian\obsidian.json), the app-wide default new vaults
// inherit. It intentionally does NOT also loop over every vault registered
// in that file and overwrite each vault's own .obsidian/app.json — the
// Python original does, but that means a vault with its own deliberate
// theme choice (e.g. a non-coding notes vault) gets silently forced to
// match Daybreak's mode too. Global-only was chosen after finding this out
// live: only touch the shared default, leave per-vault choices alone.
//
// Uses sjson for a surgical in-place set (see claudecode.go) rather than
// this package's LoadJSONCFile/DumpJSONFile, which re-sorts keys and
// reformats indentation on write.
type ObsidianAdapter struct {
	Config *config.Manager
}

func (ObsidianAdapter) Name() string { return "obsidian" }

func (a ObsidianAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	appData := os.Getenv("APPDATA")
	if appData == "" {
		return nil
	}

	def := "obsidian"
	if mode == "light" {
		def = "moonstone"
	}
	targetTheme := a.Config.GetIntegration("obsidian_"+mode+"_theme", def)

	globalPath := filepath.Join(appData, "obsidian", "obsidian.json")
	raw, err := os.ReadFile(globalPath)
	if err != nil {
		return nil
	}

	if gjson.GetBytes(raw, "theme").String() == targetTheme {
		return nil
	}

	updated, err := sjson.SetBytes(raw, "theme", targetTheme)
	if err != nil {
		log.Printf("Obsidian: failed to update %s: %v", globalPath, err)
		return nil
	}
	if err := os.WriteFile(globalPath, updated, 0o644); err != nil {
		log.Printf("Obsidian: failed writing %s: %v", globalPath, err)
		return nil
	}
	log.Printf("Obsidian: applied theme '%s' to %s", targetTheme, globalPath)
	return nil
}
