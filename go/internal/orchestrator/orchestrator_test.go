package orchestrator

import (
	"os"
	"path/filepath"
	"testing"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

func writeTestConfig(t *testing.T, path, active, light, dark, neovimDark string) {
	t.Helper()
	content := "schema_version = 2\n\n[system]\nlinux_kde_light = \"BreathLight\"\nlinux_kde_dark = \"BreathDark\"\nwindows_light_reg = 1\nwindows_dark_reg = 0\n\n[theme]\nactive = \"" +
		active + "\"\nlight = \"" + light + "\"\ndark = \"" + dark +
		"\"\n\n[integrations]\nwindows_terminal_light_scheme = \"One Half Light\"\nwindows_terminal_dark_scheme = \"One Half Dark\"\nobsidian_light_theme = \"moonstone\"\nobsidian_dark_theme = \"obsidian\"\nneovim_light_scheme = \"tokyonight-day\"\nneovim_dark_scheme = \"" +
		neovimDark + "\"\n"
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
}

// TestApplyReloadsConfigForLongLivedProcess mirrors
// tests/test_orchestrator_reload.py: apply() must re-read config.toml from
// disk each call, so a long-lived tray process picks up edits made while
// it's running.
func TestApplyReloadsConfigForLongLivedProcess(t *testing.T) {
	tmp := t.TempDir()
	configFile := filepath.Join(tmp, "config.toml")
	writeTestConfig(t, configFile, "Nord", "Nord", "Nord", "tokyonight")

	cfg := config.NewManager(tmp)
	orch := &Orchestrator{
		Config:   cfg,
		Registry: theme.NewRegistry(),
	}

	firstTheme, err := orch.Apply("dark", "")
	if err != nil {
		t.Fatal(err)
	}
	if firstTheme != "Nord" {
		t.Fatalf("first apply theme = %q, want Nord", firstTheme)
	}

	writeTestConfig(t, configFile, "One Dark", "Monokai", "One Dark", "onedark")

	secondTheme, err := orch.Apply("dark", "")
	if err != nil {
		t.Fatal(err)
	}
	if secondTheme != "One Dark" {
		t.Fatalf("second apply theme = %q, want One Dark", secondTheme)
	}
}
