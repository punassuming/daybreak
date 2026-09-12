//go:build windows

package terminal

import (
	"log"
	"os"
	"path/filepath"
	"strings"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// WindowsTerminalAdapter mirrors adapters/terminal/windows_terminal.py.
type WindowsTerminalAdapter struct {
	Config *config.Manager
}

func (WindowsTerminalAdapter) Name() string { return "windows_terminal" }

func (a WindowsTerminalAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	def := "One Half Dark"
	if mode == "light" {
		def = "One Half Light"
	}
	targetScheme := a.Config.GetIntegration("windows_terminal_"+mode+"_scheme", def)

	for _, settingsPath := range iterWindowsTerminalSettings() {
		a.applyScheme(settingsPath, targetScheme)
	}
	return nil
}

func (WindowsTerminalAdapter) applyScheme(path, targetScheme string) {
	data, err := LoadJSONCFile(path)
	if err != nil {
		log.Printf("Windows Terminal: Failed to parse %s: %v", path, err)
		return
	}

	changed := false
	profiles, ok := data["profiles"].(map[string]any)
	if !ok {
		profiles = map[string]any{}
		data["profiles"] = profiles
	}
	defaults, ok := profiles["defaults"].(map[string]any)
	if !ok {
		defaults = map[string]any{}
		profiles["defaults"] = defaults
	}
	if cs, _ := defaults["colorScheme"].(string); cs != targetScheme {
		defaults["colorScheme"] = targetScheme
		changed = true
	}

	if profileList, ok := profiles["list"].([]any); ok {
		for _, entry := range profileList {
			profileEntry, ok := entry.(map[string]any)
			if !ok {
				continue
			}
			if _, hasScheme := profileEntry["colorScheme"]; !hasScheme {
				continue
			}
			if cs, _ := profileEntry["colorScheme"].(string); cs != targetScheme {
				profileEntry["colorScheme"] = targetScheme
				changed = true
			}
		}
	}

	if changed {
		if err := DumpJSONFile(path, data); err != nil {
			log.Printf("Windows Terminal: Failed writing %s: %v", path, err)
			return
		}
		log.Printf("Windows Terminal: Applied colorScheme '%s' to %s", targetScheme, path)
	}
}

func iterWindowsTerminalSettings() []string {
	localAppData := os.Getenv("LOCALAPPDATA")
	if localAppData == "" {
		return nil
	}

	var results []string
	seen := map[string]bool{}

	packagedRoot := filepath.Join(localAppData, "Packages")
	if entries, err := os.ReadDir(packagedRoot); err == nil {
		for _, entry := range entries {
			if !entry.IsDir() || !strings.HasPrefix(entry.Name(), "Microsoft.WindowsTerminal") {
				continue
			}
			candidate := filepath.Join(packagedRoot, entry.Name(), "LocalState", "settings.json")
			if _, err := os.Stat(candidate); err == nil && !seen[candidate] {
				results = append(results, candidate)
				seen[candidate] = true
			}
		}
	}

	unpackagedCandidate := filepath.Join(localAppData, "Microsoft", "Windows Terminal", "settings.json")
	if _, err := os.Stat(unpackagedCandidate); err == nil && !seen[unpackagedCandidate] {
		results = append(results, unpackagedCandidate)
	}

	return results
}
