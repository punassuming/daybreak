package terminal

import (
	"log"
	"os"
	"path/filepath"
	"runtime"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// YaziAdapter themes yazi (the terminal file manager) by setting
// `[flavor].dark` / `[flavor].light` in theme.toml — the two flavor
// package names (installed separately via `ya pkg add`) yazi switches
// between based on the terminal's reported background.
//
// Unlike herdr/Claude Code, yazi has no bundled built-in theme catalog:
// every flavor is a separately-installed package, so there's no safe
// default to guess here. This adapter is a no-op — it neither reads nor
// creates theme.toml — until the user sets yazi_light_flavor /
// yazi_dark_flavor in daybreak's own config to flavor package names they
// have actually installed; once set, it creates theme.toml if missing
// (matching the Ghostty/WezTerm adapters' "create the include file the
// user's main config points at" pattern) or patches it in place otherwise.
type YaziAdapter struct {
	Config *config.Manager
}

func (YaziAdapter) Name() string { return "yazi" }

func (a YaziAdapter) ApplyMode(_, _ string, _ theme.Palette) error {
	lightFlavor := a.Config.GetIntegration("yazi_light_flavor", "")
	darkFlavor := a.Config.GetIntegration("yazi_dark_flavor", "")
	if lightFlavor == "" && darkFlavor == "" {
		return nil
	}

	path := yaziThemeConfigPath()
	if path == "" {
		return nil
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		if !os.IsNotExist(err) {
			log.Printf("yazi: failed to read %s: %v", path, err)
			return nil
		}
		if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
			log.Printf("yazi: failed to create %s: %v", filepath.Dir(path), err)
			return nil
		}
		raw = []byte{}
	}

	content := string(raw)
	if darkFlavor != "" {
		content = upsertTOMLKey(content, "flavor", "dark", darkFlavor)
	}
	if lightFlavor != "" {
		content = upsertTOMLKey(content, "flavor", "light", lightFlavor)
	}
	if content == string(raw) {
		return nil
	}

	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		log.Printf("yazi: failed to update %s: %v", path, err)
		return nil
	}
	log.Printf("yazi: applied flavors (dark='%s', light='%s') to %s", darkFlavor, lightFlavor, path)
	return nil
}

func yaziThemeConfigPath() string {
	if runtime.GOOS == "windows" {
		appData := os.Getenv("APPDATA")
		if appData == "" {
			return ""
		}
		return filepath.Join(appData, "yazi", "config", "theme.toml")
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return ""
	}
	return filepath.Join(home, ".config", "yazi", "theme.toml")
}
