//go:build linux

package terminal

import (
	"io"
	"log"
	"os"
	"path/filepath"

	"daybreak/internal/theme"
)

// baseConfigTerminal mirrors terminals/config_terminals.py's
// BaseConfigTerminal: overwrites a "current theme" file with the content of
// a dark/light source file that the user's terminal config includes.
type baseConfigTerminal struct {
	displayName string
	configDir   string
	themeFile   string
	darkSrc     string
	lightSrc    string
}

func newBaseConfigTerminal(name, configDir, themeFileName, darkSrc, lightSrc string) baseConfigTerminal {
	return baseConfigTerminal{
		displayName: name,
		configDir:   configDir,
		themeFile:   filepath.Join(configDir, themeFileName),
		darkSrc:     filepath.Join(configDir, "themes", darkSrc),
		lightSrc:    filepath.Join(configDir, "themes", lightSrc),
	}
}

func (t baseConfigTerminal) applyMode(mode string) {
	if _, err := os.Stat(t.configDir); err != nil {
		return
	}

	src := t.lightSrc
	if mode == "dark" {
		src = t.darkSrc
	}
	if _, err := os.Stat(src); err != nil {
		log.Printf("%s: Theme source file %s does not exist. Skipping.", t.displayName, src)
		return
	}

	if err := os.MkdirAll(filepath.Dir(t.themeFile), 0o755); err != nil {
		log.Printf("%s: Failed to update config: %v", t.displayName, err)
		return
	}
	if err := copyFile(src, t.themeFile); err != nil {
		log.Printf("%s: Failed to update config: %v", t.displayName, err)
		return
	}
	log.Printf("%s: Updated %s to %s mode.", t.displayName, t.themeFile, mode)
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer out.Close()

	_, err = io.Copy(out, in)
	return err
}

func expandHome(path string) string {
	home, err := os.UserHomeDir()
	if err != nil {
		return path
	}
	if len(path) >= 2 && path[0] == '~' && path[1] == '/' {
		return filepath.Join(home, path[2:])
	}
	return path
}

// GhosttyAdapter mirrors config_terminals.Ghostty: swaps
// ~/.config/ghostty/theme (Ghostty auto-reloads on file change).
type GhosttyAdapter struct{ inner baseConfigTerminal }

func NewGhosttyAdapter() GhosttyAdapter {
	return GhosttyAdapter{newBaseConfigTerminal("Ghostty", expandHome("~/.config/ghostty"), "theme", "dark", "light")}
}

func (GhosttyAdapter) Name() string { return "Ghostty" }

func (a GhosttyAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	a.inner.applyMode(mode)
	return nil
}

// WezTermAdapter mirrors config_terminals.WezTerm: swaps
// ~/.config/wezterm/theme.lua (WezTerm auto-reloads).
type WezTermAdapter struct{ inner baseConfigTerminal }

func NewWezTermAdapter() WezTermAdapter {
	return WezTermAdapter{newBaseConfigTerminal("WezTerm", expandHome("~/.config/wezterm"), "theme.lua", "dark.lua", "light.lua")}
}

func (WezTermAdapter) Name() string { return "WezTerm" }

func (a WezTermAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	a.inner.applyMode(mode)
	return nil
}
