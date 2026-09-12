// Package orchestrator ports core/orchestrator.py: the unified
// apply/toggle pipeline that drives the system adapter, terminal adapters,
// and generated-artifact writer for a mode switch.
package orchestrator

import (
	"log"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// SystemAdapter mirrors the Python system adapter interface
// (get_current_mode / set_mode(mode, palette)).
type SystemAdapter interface {
	GetCurrentMode() (string, error)
	SetMode(mode string, palette theme.Palette)
}

// TerminalAdapter mirrors the Python terminal adapter interface
// (apply_mode(mode, theme_name, palette), plus a name for error logging).
type TerminalAdapter interface {
	Name() string
	ApplyMode(mode, themeName string, palette theme.Palette) error
}

// ArtifactWriter matches artifacts.generate_artifacts's signature so it can
// be swapped/mocked in tests.
type ArtifactWriter func(configDir, themeName, mode string, tokens, accentTokens map[string]string, palette theme.Palette)

// Orchestrator mirrors core/orchestrator.py's ThemeOrchestrator.
type Orchestrator struct {
	Config            *config.Manager
	SystemAdapter     SystemAdapter
	TerminalAdapters  []TerminalAdapter
	Registry          *theme.Registry
	GenerateArtifacts ArtifactWriter
}

// GetCurrentMode mirrors ThemeOrchestrator.get_current_mode: defaults to
// "light" whenever there's no system adapter or detection fails.
func (o *Orchestrator) GetCurrentMode() string {
	if o.SystemAdapter == nil {
		return "light"
	}
	raw, err := o.SystemAdapter.GetCurrentMode()
	if err != nil {
		log.Printf("Failed to detect current mode. Defaulting to light: %v", err)
		return "light"
	}
	normalized, err := theme.NormalizeMode(raw)
	if err != nil {
		log.Printf("Failed to detect current mode. Defaulting to light: %v", err)
		return "light"
	}
	return normalized
}

// Apply mirrors ThemeOrchestrator.apply: reloads config, resolves the
// theme for the mode, applies it to the system + every terminal adapter
// (best-effort), writes generated artifacts, and returns the theme name
// actually applied.
func (o *Orchestrator) Apply(mode string, explicitThemeName string) (string, error) {
	o.Config.Reload()

	normalizedMode, err := theme.NormalizeMode(mode)
	if err != nil {
		return "", err
	}

	resolvedTheme := explicitThemeName
	if resolvedTheme == "" {
		resolvedTheme = o.Config.GetModeThemeName(normalizedMode)
	}

	palette, err := o.Registry.GetPalette(resolvedTheme, normalizedMode)
	if err != nil {
		return "", err
	}

	if o.SystemAdapter != nil {
		o.SystemAdapter.SetMode(normalizedMode, palette)
	}

	for _, adapter := range o.TerminalAdapters {
		if err := adapter.ApplyMode(normalizedMode, resolvedTheme, palette); err != nil {
			log.Printf("Terminal adapter '%s' failed: %v", adapter.Name(), err)
		}
	}

	if o.GenerateArtifacts != nil {
		func() {
			defer func() {
				if r := recover(); r != nil {
					log.Printf("Failed to generate theme artifacts: %v", r)
				}
			}()
			tokens, err := o.Registry.GetTokens(resolvedTheme, normalizedMode)
			if err != nil {
				log.Printf("Failed to generate theme artifacts: %v", err)
				return
			}
			accentTokens, err := o.Registry.GetAccentTokens(resolvedTheme, normalizedMode)
			if err != nil {
				log.Printf("Failed to generate theme artifacts: %v", err)
				return
			}
			o.GenerateArtifacts(o.Config.ConfigDir, resolvedTheme, normalizedMode, tokens, accentTokens, palette)
		}()
	}

	return resolvedTheme, nil
}

// ApplyToggle mirrors ThemeOrchestrator.apply_toggle.
func (o *Orchestrator) ApplyToggle(explicitThemeName string) (string, string, error) {
	targetMode := "dark"
	if o.GetCurrentMode() == "dark" {
		targetMode = "light"
	}
	themeName, err := o.Apply(targetMode, explicitThemeName)
	if err != nil {
		return "", "", err
	}
	return targetMode, themeName, nil
}
