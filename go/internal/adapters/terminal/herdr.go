package terminal

import (
	"log"
	"os"
	"path/filepath"
	"runtime"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// HerdrAdapter themes herdr (https://herdr.dev), a terminal AI-agent
// multiplexer whose config.toml has a `[theme]` table with a built-in
// `name` (catppuccin, tokyo-night, dracula, nord, gruvbox, one-dark,
// solarized, kanagawa, rose-pine, vesper, ...). Patches only the `name`
// key in place — herdr's config.toml is meant to be hand-edited and is
// heavily commented, so this never round-trips it through a TOML
// marshaler (which would strip every comment).
//
// herdr also has its own `[theme] auto_switch` / `dark_name` / `light_name`
// that follow the host terminal's appearance without any help from
// Daybreak; this adapter is for users who'd rather have Daybreak push an
// explicit theme name matching whatever Daybreak theme is active, exactly
// like every other terminal adapter in this package.
type HerdrAdapter struct {
	Config *config.Manager
}

func (HerdrAdapter) Name() string { return "herdr" }

func (a HerdrAdapter) ApplyMode(mode, _ string, _ theme.Palette) error {
	path := herdrConfigPath()
	if path == "" {
		return nil
	}
	if _, err := os.Stat(path); err != nil {
		return nil
	}

	def := "catppuccin"
	if mode == "light" {
		def = "catppuccin-latte"
	}
	targetName := a.Config.GetIntegration("herdr_"+mode+"_theme", def)

	raw, err := os.ReadFile(path)
	if err != nil {
		log.Printf("herdr: failed to read %s: %v", path, err)
		return nil
	}

	updated := upsertTOMLKey(string(raw), "theme", "name", targetName)
	if updated == string(raw) {
		return nil
	}
	if err := os.WriteFile(path, []byte(updated), 0o644); err != nil {
		log.Printf("herdr: failed to update %s: %v", path, err)
		return nil
	}
	log.Printf("herdr: applied theme '%s' to %s", targetName, path)
	return nil
}

func herdrConfigPath() string {
	if runtime.GOOS == "windows" {
		appData := os.Getenv("APPDATA")
		if appData == "" {
			return ""
		}
		return filepath.Join(appData, "herdr", "config.toml")
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".config", "herdr", "config.toml")
}
