//go:build linux

package terminal

import (
	"os/exec"

	"daybreak/internal/theme"
)

// KittyAdapter mirrors terminals/kitty.py's Kitty. The Python original also
// probed for a ~/.config/kitty/current-theme.conf symlink but the branch
// that would have swapped it was never implemented (a `pass`), so the only
// effective behavior — signaling running Kitty instances to reload — is
// what's ported here.
type KittyAdapter struct{}

func (KittyAdapter) Name() string { return "Kitty" }

func (KittyAdapter) ApplyMode(_, _ string, _ theme.Palette) error {
	_ = exec.Command("pkill", "-USR1", "kitty").Run()
	return nil
}
