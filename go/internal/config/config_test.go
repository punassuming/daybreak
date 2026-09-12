package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestMigrateLegacyTerminalThemeKeys(t *testing.T) {
	raw := map[string]any{
		"system": map[string]any{
			"linux_kde_light": "BreathLight",
			"linux_kde_dark":  "BreathDark",
		},
		"terminal": map[string]any{
			"theme":       "Nord",
			"theme_light": "Catppuccin",
			"theme_dark":  "Tokyo Night",
		},
	}

	migrated, changed := migrate(raw)

	if !changed {
		t.Fatal("expected changed=true")
	}
	if migrated.SchemaVersion != 2 {
		t.Errorf("schema_version = %d, want 2", migrated.SchemaVersion)
	}
	if migrated.Theme.Light != "Catppuccin" {
		t.Errorf("theme.light = %q, want Catppuccin", migrated.Theme.Light)
	}
	if migrated.Theme.Dark != "Tokyo Night" {
		t.Errorf("theme.dark = %q, want Tokyo Night", migrated.Theme.Dark)
	}
	// Data has no Terminal field at all, mirroring "terminal" not in migrated.
}

func TestHonorsEnvConfigDirOverride(t *testing.T) {
	tmp := t.TempDir()
	target := filepath.Join(tmp, ".daybreak-test-config")
	t.Setenv("DAYBREAK_CONFIG_DIR", target)

	m := NewManager("")
	if m.ConfigDir != target {
		t.Errorf("ConfigDir = %q, want %q", m.ConfigDir, target)
	}
}

func TestMigrationBackfillsNeovimIntegrationKeys(t *testing.T) {
	raw := map[string]any{
		"schema_version": int64(2),
		"system": map[string]any{
			"linux_kde_light": "BreathLight",
			"linux_kde_dark":  "BreathDark",
		},
		"theme": map[string]any{
			"active": "Nord",
			"light":  "Nord",
			"dark":   "Nord",
		},
		"integrations": map[string]any{
			"windows_terminal_light_scheme": "One Half Light",
			"windows_terminal_dark_scheme":  "One Half Dark",
			"obsidian_light_theme":          "moonstone",
			"obsidian_dark_theme":           "obsidian",
		},
	}

	migrated, changed := migrate(raw)

	if !changed {
		t.Fatal("expected changed=true")
	}
	if migrated.Integrations.NeovimLightScheme != "tokyonight-day" {
		t.Errorf("neovim_light_scheme = %q, want tokyonight-day", migrated.Integrations.NeovimLightScheme)
	}
	if migrated.Integrations.NeovimDarkScheme != "tokyonight" {
		t.Errorf("neovim_dark_scheme = %q, want tokyonight", migrated.Integrations.NeovimDarkScheme)
	}
}

func TestReloadReflectsUpdatedFileContents(t *testing.T) {
	tmp := t.TempDir()
	configFile := filepath.Join(tmp, "config.toml")

	writeConfig := func(active, light, dark, neovimDark string) {
		content := []byte(
			"schema_version = 2\n\n[system]\nlinux_kde_light = \"BreathLight\"\nlinux_kde_dark = \"BreathDark\"\nwindows_light_reg = 1\nwindows_dark_reg = 0\n\n[theme]\nactive = \"" + active + "\"\nlight = \"" + light + "\"\ndark = \"" + dark + "\"\n\n[integrations]\nwindows_terminal_light_scheme = \"One Half Light\"\nwindows_terminal_dark_scheme = \"One Half Dark\"\nobsidian_light_theme = \"moonstone\"\nobsidian_dark_theme = \"obsidian\"\nneovim_light_scheme = \"tokyonight-day\"\nneovim_dark_scheme = \"" + neovimDark + "\"\n",
		)
		if err := os.WriteFile(configFile, content, 0o644); err != nil {
			t.Fatal(err)
		}
	}

	writeConfig("Nord", "Nord", "Nord", "tokyonight")

	m := NewManager(tmp)
	if got := m.GetModeThemeName("dark"); got != "Nord" {
		t.Fatalf("initial dark theme = %q, want Nord", got)
	}

	writeConfig("One Dark", "Monokai", "One Dark", "onedark")
	m.Reload()

	if got := m.GetModeThemeName("dark"); got != "One Dark" {
		t.Errorf("reloaded dark theme = %q, want One Dark", got)
	}
	if got := m.Data.Integrations.NeovimDarkScheme; got != "onedark" {
		t.Errorf("reloaded neovim_dark_scheme = %q, want onedark", got)
	}
}
