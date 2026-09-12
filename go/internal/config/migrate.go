package config

// migrate mirrors ConfigManager._migrate: fills in missing fields with
// defaults, migrates the legacy [terminal] table into [theme], and reports
// whether anything changed (so callers know to persist the result).
func migrate(raw map[string]any) (Data, bool) {
	changed := false
	def := defaultData()

	schemaVersion, _ := raw["schema_version"].(int64)
	if int(schemaVersion) != CurrentSchemaVersion {
		changed = true
	}

	systemRaw, systemIsMap := asMap(raw["system"])
	if !systemIsMap {
		changed = true
		systemRaw = map[string]any{}
	}
	system := System{
		LinuxKDELight:       stringOrDefault(systemRaw, "linux_kde_light", def.System.LinuxKDELight, &changed),
		LinuxKDEDark:        stringOrDefault(systemRaw, "linux_kde_dark", def.System.LinuxKDEDark, &changed),
		WindowsLightReg:     intOrDefault(systemRaw, "windows_light_reg", def.System.WindowsLightReg, &changed),
		WindowsDarkReg:      intOrDefault(systemRaw, "windows_dark_reg", def.System.WindowsDarkReg, &changed),
		WindowsCursorLight:  stringOrDefault(systemRaw, "windows_cursor_light", def.System.WindowsCursorLight, &changed),
		WindowsCursorDark:   stringOrDefault(systemRaw, "windows_cursor_dark", def.System.WindowsCursorDark, &changed),
		LinuxKDECursorLight: stringOrDefault(systemRaw, "linux_kde_cursor_light", def.System.LinuxKDECursorLight, &changed),
		LinuxKDECursorDark:  stringOrDefault(systemRaw, "linux_kde_cursor_dark", def.System.LinuxKDECursorDark, &changed),
	}

	legacyTerminal, _ := asMap(raw["terminal"])

	themeRaw, themeIsMap := asMap(raw["theme"])
	if !themeIsMap {
		changed = true
		themeRaw = map[string]any{}
	}

	active := firstNonEmpty(
		stringVal(themeRaw, "active"),
		stringVal(legacyTerminal, "theme"),
		def.Theme.Active,
	)
	light := firstNonEmpty(
		stringVal(themeRaw, "light"),
		stringVal(legacyTerminal, "theme_light"),
		active,
	)
	dark := firstNonEmpty(
		stringVal(themeRaw, "dark"),
		stringVal(legacyTerminal, "theme_dark"),
		active,
	)

	if stringVal(themeRaw, "active") != active ||
		stringVal(themeRaw, "light") != light ||
		stringVal(themeRaw, "dark") != dark ||
		len(themeRaw) != 3 {
		changed = true
	}
	theme := Theme{Active: active, Light: light, Dark: dark}

	integrationsRaw, integrationsIsMap := asMap(raw["integrations"])
	if !integrationsIsMap {
		changed = true
		integrationsRaw = map[string]any{}
	}
	integrations := Integrations{
		WindowsTerminalLightScheme: stringOrDefault(integrationsRaw, "windows_terminal_light_scheme", def.Integrations.WindowsTerminalLightScheme, &changed),
		WindowsTerminalDarkScheme:  stringOrDefault(integrationsRaw, "windows_terminal_dark_scheme", def.Integrations.WindowsTerminalDarkScheme, &changed),
		ObsidianLightTheme:         stringOrDefault(integrationsRaw, "obsidian_light_theme", def.Integrations.ObsidianLightTheme, &changed),
		ObsidianDarkTheme:          stringOrDefault(integrationsRaw, "obsidian_dark_theme", def.Integrations.ObsidianDarkTheme, &changed),
		NeovimLightScheme:          stringOrDefault(integrationsRaw, "neovim_light_scheme", def.Integrations.NeovimLightScheme, &changed),
		NeovimDarkScheme:           stringOrDefault(integrationsRaw, "neovim_dark_scheme", def.Integrations.NeovimDarkScheme, &changed),
		HerdrLightTheme:            stringOrDefault(integrationsRaw, "herdr_light_theme", def.Integrations.HerdrLightTheme, &changed),
		HerdrDarkTheme:             stringOrDefault(integrationsRaw, "herdr_dark_theme", def.Integrations.HerdrDarkTheme, &changed),
		YaziLightFlavor:            stringOrDefault(integrationsRaw, "yazi_light_flavor", def.Integrations.YaziLightFlavor, &changed),
		YaziDarkFlavor:             stringOrDefault(integrationsRaw, "yazi_dark_flavor", def.Integrations.YaziDarkFlavor, &changed),
		ClaudeCodeLightTheme:       stringOrDefault(integrationsRaw, "claude_code_light_theme", def.Integrations.ClaudeCodeLightTheme, &changed),
		ClaudeCodeDarkTheme:        stringOrDefault(integrationsRaw, "claude_code_dark_theme", def.Integrations.ClaudeCodeDarkTheme, &changed),
		CodexLightTheme:            stringOrDefault(integrationsRaw, "codex_light_theme", def.Integrations.CodexLightTheme, &changed),
		CodexDarkTheme:             stringOrDefault(integrationsRaw, "codex_dark_theme", def.Integrations.CodexDarkTheme, &changed),
	}

	if _, hasTerminal := raw["terminal"]; hasTerminal {
		changed = true
	}

	return Data{
		SchemaVersion: CurrentSchemaVersion,
		System:        system,
		Theme:         theme,
		Integrations:  integrations,
	}, changed
}

func asMap(v any) (map[string]any, bool) {
	m, ok := v.(map[string]any)
	return m, ok
}

func stringVal(m map[string]any, key string) string {
	if m == nil {
		return ""
	}
	s, _ := m[key].(string)
	return s
}

func stringOrDefault(m map[string]any, key, def string, changed *bool) string {
	if v, ok := m[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	*changed = true
	return def
}

func intOrDefault(m map[string]any, key string, def int, changed *bool) int {
	if v, ok := m[key]; ok {
		if i, ok := v.(int64); ok {
			return int(i)
		}
	}
	*changed = true
	return def
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if v != "" {
			return v
		}
	}
	return ""
}
