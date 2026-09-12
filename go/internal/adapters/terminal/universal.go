//go:build linux

package terminal

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// UniversalPtyAdapter mirrors terminals/universal.py's UniversalPty (wrapped
// by adapters/terminal/wrappers.py's UniversalPtyAdapter): broadcasts full
// 16-color OSC escape sequences to every open PTY and writes shell scripts
// so new terminals pick up the theme too.
type UniversalPtyAdapter struct {
	Config *config.Manager
}

func (UniversalPtyAdapter) Name() string { return "universal_pty" }

func (a UniversalPtyAdapter) ApplyMode(mode, themeName string, _ theme.Palette) error {
	a.applyTheme(themeName, mode)
	return nil
}

func (UniversalPtyAdapter) applyTheme(themeName, mode string) {
	paletteSet := theme.GetThemePalette(themeName)
	var pal theme.Palette
	if mode == "light" {
		pal = paletteSet.Light
	} else {
		pal = paletteSet.Dark
	}
	if pal.Colors == nil && pal.Special == nil {
		log.Printf("Theme '%s' does not support %s mode.", themeName, mode)
		return
	}

	var sb strings.Builder
	fmt.Fprintf(&sb, "\033]10;%s\007", pal.Special["foreground"])
	fmt.Fprintf(&sb, "\033]11;%s\007", pal.Special["background"])
	fmt.Fprintf(&sb, "\033]12;%s\007", pal.Special["cursor"])

	for i := 0; i <= 15; i++ {
		key := strconv.Itoa(i)
		if color, ok := pal.Colors[key]; ok {
			fmt.Fprintf(&sb, "\033]4;%s;%s\007", key, color)
		}
	}

	payload := sb.String()
	broadcast(payload)
	writeShellScripts(payload)
}

func broadcast(payload string) {
	matches, err := filepath.Glob("/dev/pts/[0-9]*")
	if err != nil {
		return
	}
	count := 0
	for _, ptyPath := range matches {
		f, err := os.OpenFile(ptyPath, os.O_WRONLY, 0)
		if err != nil {
			continue
		}
		if _, err := f.WriteString(payload); err == nil {
			count++
		}
		f.Close()
	}
	if count > 0 {
		log.Printf("Broadcasted palette to %d terminals.", count)
	}
}

func writeShellScripts(payload string) {
	home, err := os.UserHomeDir()
	if err != nil {
		return
	}
	configDir := filepath.Join(home, ".config", "daybreak")
	if err := os.MkdirAll(configDir, 0o755); err != nil {
		return
	}

	if err := os.WriteFile(filepath.Join(configDir, "theme.sh"), []byte("#!/bin/sh\nprintf '"+payload+"'\n"), 0o644); err != nil {
		log.Printf("Failed to write theme.sh: %v", err)
	}

	if err := os.WriteFile(filepath.Join(configDir, "theme.fish"), []byte("printf '"+payload+"'\n"), 0o644); err != nil {
		log.Printf("Failed to write theme.fish: %v", err)
	}

	psPayload := strings.ReplaceAll(payload, "\033", "$([char]0x1b)")
	if err := os.WriteFile(filepath.Join(configDir, "theme.ps1"), []byte("Write-Host \""+psPayload+"\" -NoNewline\n"), 0o644); err != nil {
		log.Printf("Failed to write theme.ps1: %v", err)
	}
}
