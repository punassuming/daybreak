// Package config ports daybreak's config.py: TOML-backed settings with
// schema migration, kept at ~/.config/daybreak/config.toml (or
// $DAYBREAK_CONFIG_DIR) so existing Python-era config files keep working
// unchanged after switching to this binary.
package config

import (
	"log"
	"os"
	"path/filepath"

	toml "github.com/pelletier/go-toml/v2"
)

const CurrentSchemaVersion = 2

// System mirrors the [system] table.
type System struct {
	LinuxKDELight   string `toml:"linux_kde_light"`
	LinuxKDEDark    string `toml:"linux_kde_dark"`
	WindowsLightReg int    `toml:"windows_light_reg"`
	WindowsDarkReg  int    `toml:"windows_dark_reg"`
	// Cursor theme/scheme names, applied alongside the color scheme when
	// set. Left blank by default (opt-in): a wrong guess here would point
	// SystemParametersInfo/plasma-apply-cursortheme at a scheme the user
	// hasn't actually installed.
	WindowsCursorLight  string `toml:"windows_cursor_light"`
	WindowsCursorDark   string `toml:"windows_cursor_dark"`
	LinuxKDECursorLight string `toml:"linux_kde_cursor_light"`
	LinuxKDECursorDark  string `toml:"linux_kde_cursor_dark"`
}

// Theme mirrors the [theme] table.
type Theme struct {
	Active string `toml:"active"`
	Light  string `toml:"light"`
	Dark   string `toml:"dark"`
}

// Integrations mirrors the [integrations] table.
type Integrations struct {
	WindowsTerminalLightScheme string `toml:"windows_terminal_light_scheme"`
	WindowsTerminalDarkScheme  string `toml:"windows_terminal_dark_scheme"`
	ObsidianLightTheme         string `toml:"obsidian_light_theme"`
	ObsidianDarkTheme          string `toml:"obsidian_dark_theme"`
	NeovimLightScheme          string `toml:"neovim_light_scheme"`
	NeovimDarkScheme           string `toml:"neovim_dark_scheme"`
	HerdrLightTheme            string `toml:"herdr_light_theme"`
	HerdrDarkTheme             string `toml:"herdr_dark_theme"`
	YaziLightFlavor            string `toml:"yazi_light_flavor"`
	YaziDarkFlavor             string `toml:"yazi_dark_flavor"`
	ClaudeCodeLightTheme       string `toml:"claude_code_light_theme"`
	ClaudeCodeDarkTheme        string `toml:"claude_code_dark_theme"`
	CodexLightTheme            string `toml:"codex_light_theme"`
	CodexDarkTheme             string `toml:"codex_dark_theme"`
}

// Data is the full config document, mirroring DEFAULT_CONFIG's shape.
type Data struct {
	SchemaVersion int          `toml:"schema_version"`
	System        System       `toml:"system"`
	Theme         Theme        `toml:"theme"`
	Integrations  Integrations `toml:"integrations"`
}

func defaultData() Data {
	return Data{
		SchemaVersion: CurrentSchemaVersion,
		System: System{
			LinuxKDELight:       "BreathLight",
			LinuxKDEDark:        "BreathDark",
			WindowsLightReg:     1,
			WindowsDarkReg:      0,
			WindowsCursorLight:  "",
			WindowsCursorDark:   "",
			LinuxKDECursorLight: "",
			LinuxKDECursorDark:  "",
		},
		Theme: Theme{
			Active: "Nord",
			Light:  "Nord",
			Dark:   "Nord",
		},
		Integrations: Integrations{
			WindowsTerminalLightScheme: "One Half Light",
			WindowsTerminalDarkScheme:  "One Half Dark",
			ObsidianLightTheme:         "moonstone",
			ObsidianDarkTheme:          "obsidian",
			NeovimLightScheme:          "tokyonight-day",
			NeovimDarkScheme:           "tokyonight",
			// Herdr, Claude Code, and Codex ship these as built-in presets
			// (Codex's confirmed live via its own /theme picker), so they're
			// always valid out of the box. Yazi flavors are left blank by
			// default (opt-in) because the correct value depends on which
			// flavor package the user has separately installed — a wrong
			// guess here would point yazi at something that doesn't exist.
			HerdrLightTheme:      "catppuccin-latte",
			HerdrDarkTheme:       "catppuccin",
			YaziLightFlavor:      "",
			YaziDarkFlavor:       "",
			ClaudeCodeLightTheme: "light",
			ClaudeCodeDarkTheme:  "dark",
			CodexLightTheme:      "one-half-light",
			CodexDarkTheme:       "one-half-dark",
		},
	}
}

// Manager mirrors ConfigManager.
type Manager struct {
	ConfigDir  string
	ConfigFile string
	Data       Data
}

// NewManager mirrors ConfigManager.__init__: configDir empty means resolve
// from $DAYBREAK_CONFIG_DIR, else ~/.config/daybreak.
func NewManager(configDir string) *Manager {
	if configDir == "" {
		if env := os.Getenv("DAYBREAK_CONFIG_DIR"); env != "" {
			configDir = env
		} else {
			home, err := os.UserHomeDir()
			if err != nil {
				home = "."
			}
			configDir = filepath.Join(home, ".config", "daybreak")
		}
	}
	m := &Manager{
		ConfigDir:  configDir,
		ConfigFile: filepath.Join(configDir, "config.toml"),
	}
	m.Data = m.load()
	return m
}

func (m *Manager) load() Data {
	raw, err := os.ReadFile(m.ConfigFile)
	if err != nil {
		if os.IsNotExist(err) {
			return m.createDefault()
		}
		log.Printf("Failed to load config: %v. Using defaults.", err)
		return defaultData()
	}

	var loaded map[string]any
	if err := toml.Unmarshal(raw, &loaded); err != nil {
		log.Printf("Failed to load config: %v. Using defaults.", err)
		return defaultData()
	}

	migrated, changed := migrate(loaded)
	if changed {
		if err := m.save(migrated); err != nil {
			log.Printf("Failed to write migrated config: %v", err)
		}
	}
	return migrated
}

func (m *Manager) createDefault() Data {
	data := defaultData()
	if err := m.save(data); err != nil {
		log.Printf("Failed to persist default config: %v", err)
	} else {
		log.Printf("Created default config at %s", m.ConfigFile)
	}
	return data
}

func (m *Manager) save(data Data) error {
	if err := os.MkdirAll(m.ConfigDir, 0o755); err != nil {
		return err
	}
	out, err := toml.Marshal(data)
	if err != nil {
		return err
	}
	return os.WriteFile(m.ConfigFile, out, 0o644)
}

// Save mirrors ConfigManager.save (best-effort, logs on failure).
func (m *Manager) Save() {
	if err := m.save(m.Data); err != nil {
		log.Printf("Failed to save config: %v", err)
	}
}

// Reload mirrors ConfigManager.reload.
func (m *Manager) Reload() {
	m.Data = m.load()
}

// GetSystemTheme mirrors ConfigManager.get_system_theme (osType "linux_kde" only).
func (m *Manager) GetSystemTheme(osType, mode string) string {
	if osType != "linux_kde" {
		return ""
	}
	if mode == "light" {
		return m.Data.System.LinuxKDELight
	}
	return m.Data.System.LinuxKDEDark
}

// GetActiveThemeName mirrors ConfigManager.get_active_theme_name.
func (m *Manager) GetActiveThemeName() string {
	return m.Data.Theme.Active
}

// GetModeThemeName mirrors ConfigManager.get_mode_theme_name.
func (m *Manager) GetModeThemeName(mode string) string {
	switch mode {
	case "light":
		if m.Data.Theme.Light != "" {
			return m.Data.Theme.Light
		}
	case "dark":
		if m.Data.Theme.Dark != "" {
			return m.Data.Theme.Dark
		}
	}
	return m.GetActiveThemeName()
}

// GetIntegration mirrors ConfigManager.get("integrations", key, default) for
// the dynamically-keyed integration lookups terminal adapters make
// (windows_terminal_{mode}_scheme, obsidian_{mode}_theme,
// neovim_{light,dark}_scheme). Integrations has fixed Go struct fields, so
// this maps the runtime key string onto the right field.
func (m *Manager) GetIntegration(key, def string) string {
	orDefault := func(v string) string {
		if v != "" {
			return v
		}
		return def
	}
	switch key {
	case "windows_terminal_light_scheme":
		return orDefault(m.Data.Integrations.WindowsTerminalLightScheme)
	case "windows_terminal_dark_scheme":
		return orDefault(m.Data.Integrations.WindowsTerminalDarkScheme)
	case "obsidian_light_theme":
		return orDefault(m.Data.Integrations.ObsidianLightTheme)
	case "obsidian_dark_theme":
		return orDefault(m.Data.Integrations.ObsidianDarkTheme)
	case "neovim_light_scheme":
		return orDefault(m.Data.Integrations.NeovimLightScheme)
	case "neovim_dark_scheme":
		return orDefault(m.Data.Integrations.NeovimDarkScheme)
	case "herdr_light_theme":
		return orDefault(m.Data.Integrations.HerdrLightTheme)
	case "herdr_dark_theme":
		return orDefault(m.Data.Integrations.HerdrDarkTheme)
	case "yazi_light_flavor":
		return orDefault(m.Data.Integrations.YaziLightFlavor)
	case "yazi_dark_flavor":
		return orDefault(m.Data.Integrations.YaziDarkFlavor)
	case "claude_code_light_theme":
		return orDefault(m.Data.Integrations.ClaudeCodeLightTheme)
	case "claude_code_dark_theme":
		return orDefault(m.Data.Integrations.ClaudeCodeDarkTheme)
	case "codex_light_theme":
		return orDefault(m.Data.Integrations.CodexLightTheme)
	case "codex_dark_theme":
		return orDefault(m.Data.Integrations.CodexDarkTheme)
	default:
		return def
	}
}

// SetModeThemes mirrors ConfigManager.set_mode_themes.
func (m *Manager) SetModeThemes(lightTheme, darkTheme string) {
	m.Data.Theme.Light = lightTheme
	m.Data.Theme.Dark = darkTheme
	if m.Data.Theme.Active == "" {
		m.Data.Theme.Active = darkTheme
	}
	m.Save()
}
