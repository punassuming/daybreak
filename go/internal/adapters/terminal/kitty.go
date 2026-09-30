//go:build linux

package terminal

import (
	"fmt"
	"os"
	"os/exec"
	"sort"
	"strconv"
	"strings"

	"daybreak/internal/theme"
)

// KittyAdapter applies the active Daybreak palette to running Kitty windows.
// Kitty's remote-control command updates both current and configured colors,
// so subsequent windows and color resets follow the selected Daybreak mode.
type KittyAdapter struct{ ConfigDir string }

func (KittyAdapter) Name() string { return "Kitty" }

func (a KittyAdapter) ApplyMode(_, _ string, palette theme.Palette) error {
	config, err := kittyPaletteConfig(palette)
	if err != nil {
		return err
	}
	dir := a.ConfigDir
	if dir == "" {
		dir = os.TempDir()
	}
	file, err := os.CreateTemp(dir, "daybreak-kitty-*.conf")
	if err != nil {
		return fmt.Errorf("kitty: create palette file: %w", err)
	}
	path := file.Name()
	defer os.Remove(path)
	if _, err := file.WriteString(config); err != nil {
		file.Close()
		return fmt.Errorf("kitty: write palette file: %w", err)
	}
	if err := file.Close(); err != nil {
		return fmt.Errorf("kitty: close palette file: %w", err)
	}
	if err := exec.Command("kitty", "@", "set-colors", "--all", "--configured", path).Run(); err != nil {
		return fmt.Errorf("kitty: apply colors (ensure remote control is enabled): %w", err)
	}
	return nil
}

func kittyPaletteConfig(p theme.Palette) (string, error) {
	var lines []string
	for _, key := range []string{"background", "foreground", "cursor"} {
		if color := p.Special[key]; color != "" {
			lines = append(lines, key+" "+color)
		}
	}
	keys := make([]int, 0, len(p.Colors))
	for key := range p.Colors {
		n, err := strconv.Atoi(key)
		if err != nil || n < 0 || n > 255 {
			return "", fmt.Errorf("kitty: invalid palette color index %q", key)
		}
		keys = append(keys, n)
	}
	sort.Ints(keys)
	for _, key := range keys {
		lines = append(lines, fmt.Sprintf("color%d %s", key, p.Colors[strconv.Itoa(key)]))
	}
	return strings.Join(lines, "\n") + "\n", nil
}
