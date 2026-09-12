//go:build windows

package terminal

import (
	"log"
	"os"
	"path/filepath"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// ObsidianAdapter mirrors adapters/terminal/obsidian.py.
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
	if _, err := os.Stat(globalPath); err != nil {
		return nil
	}

	var vaultPaths []string
	globalData, err := LoadJSONCFile(globalPath)
	if err != nil {
		log.Printf("Obsidian: Failed to update %s: %v", globalPath, err)
	} else {
		changed := false
		if cur, _ := globalData["theme"].(string); cur != targetTheme {
			globalData["theme"] = targetTheme
			changed = true
		}
		vaultPaths = extractVaultPaths(globalData)

		if changed {
			if err := DumpJSONFile(globalPath, globalData); err != nil {
				log.Printf("Obsidian: Failed to update %s: %v", globalPath, err)
			} else {
				log.Printf("Obsidian: Applied theme '%s' to %s", targetTheme, globalPath)
			}
		}
	}

	for _, vaultPath := range vaultPaths {
		appJSON := filepath.Join(vaultPath, ".obsidian", "app.json")
		if _, err := os.Stat(appJSON); err != nil {
			continue
		}
		appDataJSON, err := LoadJSONCFile(appJSON)
		if err != nil {
			log.Printf("Obsidian: Failed to update %s: %v", appJSON, err)
			continue
		}
		if cur, _ := appDataJSON["theme"].(string); cur == targetTheme {
			continue
		}
		appDataJSON["theme"] = targetTheme
		if err := DumpJSONFile(appJSON, appDataJSON); err != nil {
			log.Printf("Obsidian: Failed to update %s: %v", appJSON, err)
			continue
		}
		log.Printf("Obsidian: Applied theme '%s' to %s", targetTheme, appJSON)
	}

	return nil
}

func extractVaultPaths(globalData map[string]any) []string {
	vaults, ok := globalData["vaults"].(map[string]any)
	if !ok {
		return nil
	}

	var results []string
	for _, entry := range vaults {
		vaultEntry, ok := entry.(map[string]any)
		if !ok {
			continue
		}
		pathValue, ok := vaultEntry["path"].(string)
		if !ok || pathValue == "" {
			continue
		}
		if _, err := os.Stat(pathValue); err == nil {
			results = append(results, pathValue)
		}
	}
	return results
}
