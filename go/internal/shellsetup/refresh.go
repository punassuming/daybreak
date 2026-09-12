package shellsetup

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"

	"daybreak/internal/adapters/terminal"
	"daybreak/internal/orchestrator"
)

// RefreshGeneratedArtifacts mirrors shell_setup.refresh_generated_artifacts:
// best-effort, regenerates Daybreak-owned shared artifacts and Neovim
// helper files for the currently-detected (or last-known) mode, without
// forcing a full system/terminal mode apply.
func RefreshGeneratedArtifacts(orch *orchestrator.Orchestrator) {
	mode := detectMode(orch)

	if changed, err := normalizeIntegrationsSectionFile(orch.Config.ConfigFile); err == nil && changed {
		log.Printf("Normalized duplicate integrations sections in %s", orch.Config.ConfigFile)
	}

	defer func() {
		if r := recover(); r != nil {
			log.Printf("Failed to refresh Daybreak generated artifacts: %v", r)
		}
	}()

	themeName := orch.Config.GetModeThemeName(mode)
	palette, err := orch.Registry.GetPalette(themeName, mode)
	if err != nil {
		log.Printf("Failed to refresh Daybreak generated artifacts: %v", err)
		return
	}
	tokens, err := orch.Registry.GetTokens(themeName, mode)
	if err != nil {
		log.Printf("Failed to refresh Daybreak generated artifacts: %v", err)
		return
	}
	accentTokens, err := orch.Registry.GetAccentTokens(themeName, mode)
	if err != nil {
		log.Printf("Failed to refresh Daybreak generated artifacts: %v", err)
		return
	}
	if orch.GenerateArtifacts != nil {
		orch.GenerateArtifacts(orch.Config.ConfigDir, themeName, mode, tokens, accentTokens, palette)
	}

	neovim := terminal.NewNeovimAdapter(orch.Config)
	neovim.GenerateHelperPlugin()
	neovim.GenerateBootstrapPlugin()
	_ = neovim.ApplyMode(mode, themeName, palette)

	log.Printf("Refreshed Daybreak generated artifacts (%s: %s).", mode, themeName)
}

// detectMode mirrors the "prefer runtime-detected mode, else last generated
// mode from palette.json, else light" fallback chain in
// refresh_generated_artifacts.
func detectMode(orch *orchestrator.Orchestrator) string {
	if orch.SystemAdapter != nil {
		mode := orch.GetCurrentMode()
		if mode == "light" || mode == "dark" {
			return mode
		}
	}

	palettePath := filepath.Join(orch.Config.ConfigDir, "palette.json")
	if raw, err := os.ReadFile(palettePath); err == nil {
		var data struct {
			Mode string `json:"mode"`
		}
		if err := json.Unmarshal(raw, &data); err == nil {
			if data.Mode == "light" || data.Mode == "dark" {
				return data.Mode
			}
		}
	}

	return "light"
}

func normalizeIntegrationsSectionFile(path string) (bool, error) {
	original, err := os.ReadFile(path)
	if err != nil {
		return false, err
	}
	normalized := normalizeIntegrationsSectionText(string(original))
	if normalized == string(original) {
		return false, nil
	}
	return true, os.WriteFile(path, []byte(normalized), 0o644)
}
