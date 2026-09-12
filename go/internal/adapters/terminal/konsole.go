//go:build linux

package terminal

import (
	"bufio"
	"log"
	"os"
	"path/filepath"
	"strings"

	"daybreak/internal/theme"
	"gopkg.in/ini.v1"
)

// KonsoleAdapter mirrors terminals/konsole.py's Konsole.
type KonsoleAdapter struct{}

func (KonsoleAdapter) Name() string { return "Konsole" }

func (KonsoleAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	home, err := os.UserHomeDir()
	if err != nil {
		return nil
	}

	configPath := filepath.Join(home, ".config", "konsolerc")
	if _, err := os.Stat(configPath); err != nil {
		return nil
	}

	defaultProfileName := readDefaultProfileName(configPath)

	profilePath := filepath.Join(home, ".local", "share", "konsole", defaultProfileName)
	if filepath.Ext(profilePath) != ".profile" {
		profilePath += ".profile"
	}
	if _, err := os.Stat(profilePath); err != nil {
		log.Printf("Konsole profile %s not found.", profilePath)
		return nil
	}

	targetScheme := "BreezeDark"
	if mode == "light" {
		targetScheme = "Breeze"
	}

	profileCfg, err := ini.LoadSources(ini.LoadOptions{IgnoreInlineComment: true}, profilePath)
	if err != nil {
		log.Printf("Konsole: Failed to update profile: %v", err)
		return nil
	}
	profileCfg.Section("Appearance").Key("ColorScheme").SetValue(targetScheme)
	if err := profileCfg.SaveTo(profilePath); err != nil {
		log.Printf("Konsole: Failed to update profile: %v", err)
		return nil
	}

	log.Printf("Konsole: Updated profile %s to %s", defaultProfileName, targetScheme)
	return nil
}

func readDefaultProfileName(configPath string) string {
	f, err := os.Open(configPath)
	if err != nil {
		return "Default"
	}
	defer f.Close()

	inDesktopEntry := false
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if strings.HasPrefix(line, "[") && strings.HasSuffix(line, "]") {
			inDesktopEntry = line == "[Desktop Entry]"
			continue
		}
		if inDesktopEntry && strings.HasPrefix(line, "DefaultProfile") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				return strings.TrimSpace(parts[1])
			}
		}
	}
	return "Default"
}
