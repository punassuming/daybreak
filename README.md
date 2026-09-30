# Daybreak 🌅

Daybreak is a Go command-line app that switches the system and supported applications between light and dark appearances. It also publishes the active palette for shell prompts and other tools, provides an interactive theme selector, and can install launchers and shell hooks.

The CLI is supported on Windows and Linux. Linux desktop integration is KDE-first. Individual application integrations are best-effort: Daybreak skips apps whose expected config files or running processes are absent, and a failure in one integration does not stop the other integrations.

## What Daybreak changes

| Area | Windows | Linux |
| --- | --- | --- |
| System appearance | Sets the Windows app and system light/dark registry values, then broadcasts a settings change. | Applies the configured KDE color scheme and the Breath light/dark Plasma style. |
| Optional cursor appearance | Applies a configured, previously saved Windows cursor scheme. | Applies a configured KDE cursor theme. |
| Terminals and tools | Windows Terminal, Herdr, Yazi, Claude Code, and Codex CLI. | Kitty, Konsole, Ghostty, WezTerm, Neovim, Herdr, Yazi, Claude Code, and Codex CLI. |
| Running terminal sessions | No general terminal broadcast. | Sends the active ANSI palette to writable local PTYs and updates their foreground, background, and cursor with OSC sequences. Kitty is also updated through its remote-control interface. |
| Tray | Native Windows tray icon and actions. | StatusNotifierItem tray icon over the KDE session D-Bus. |

Application adapters update an app's settings or active colors where supported. They do not install third-party themes. Ghostty and WezTerm need the theme source files already installed and their main config must include Daybreak's current theme file. Yazi flavor switching is off until installed flavors are configured. Codex's `tui.theme` selects its built-in TUI theme; Codex controls which surfaces that setting recolors.

### Integration details and requirements

- **KDE Plasma:** `plasma-apply-colorscheme` applies `[system].linux_kde_light` or `linux_kde_dark`; `plasma-apply-desktoptheme` applies `breath-light` or `breath-dark`. If the desktop-theme command is unavailable, Daybreak tries a `plasmarc` write. The generated `DaybreakTheme.colors` scheme is available if selected explicitly in Daybreak's config. Cursor settings are optional.
- **Windows:** Daybreak changes `AppsUseLightTheme` and `SystemUsesLightTheme` under the current user's Personalize registry key and broadcasts `WM_SETTINGCHANGE`. Optional cursor schemes must already be saved in Windows' cursor scheme registry.
- **Kitty:** Sends the selected Daybreak palette to all running Kitty windows and updates configured colors through `kitty @ set-colors`. Kitty remote control must be enabled in Kitty's configuration.
- **Konsole:** Updates the color scheme on the profile selected as the default profile in `konsolerc`. Uses Breeze for light and BreezeDark for dark.
- **Ghostty and WezTerm:** Copies user-provided light/dark source files to `~/.config/ghostty/theme` or `~/.config/wezterm/theme.lua`. The main app config needs to reference the destination file. Ghostty/WezTerm reload their config when changed.
- **Neovim:** Writes `theme.lua` and Lua bootstrap/watcher helpers in Daybreak's config directory. Add `dofile(vim.fn.expand("~/.config/daybreak/nvim_bootstrap.lua"))` to `init.lua` to enable startup loading, live updates, and the `:DaybreakToggle` command. Scheme names are configurable; the scheme/plugin must be installed in Neovim.
- **Herdr:** Updates `[theme].name` in the existing Herdr `config.toml`, then asks a running Herdr server to reload its config. Defaults are Catppuccin Latte and Catppuccin. Herdr's `auto_switch` is independent; Daybreak sets the explicit theme on each apply.
- **Yazi:** When `yazi_light_flavor` or `yazi_dark_flavor` is set, patches `[flavor].light` and `[flavor].dark` in Yazi's `theme.toml`. The configured flavors must be installed. With both values blank, this adapter does nothing.
- **Claude Code:** Updates the `theme` key in an existing `~/.claude/settings.json`, using its built-in light/dark themes by default.
- **Codex CLI:** Updates `[tui].theme` in an existing `~/.codex/config.toml` to `one-half-light` or `one-half-dark` by default. This controls Codex's selected TUI theme; Codex documents syntax highlighting for fenced code and diffs, and may not recolor every UI surface such as the composer.
- **Windows Terminal:** Updates the default color scheme and profiles that already have a `colorScheme` entry in the discovered `settings.json` file(s). Scheme names are configurable.
- **Obsidian:** Updates the global theme default in `%APPDATA%\obsidian\obsidian.json` (Moonstone / Obsidian by default). Per-vault theme choices are left alone.

## Themes

Built-in themes are **Catppuccin, Dracula, Gruvbox, Monokai, Nord, One Dark, Solarized, and Tokyo Night**. Each theme provides at least one mode. Daybreak generates a paired light or dark palette when the library only defines one mode. Unknown theme names fall back to Nord.

The palette includes background, foreground, cursor, ANSI colors, and generated extended colors. Daybreak derives semantic and accent tokens using its contrast utilities. `daybreak select` previews themes in both modes and lets you choose separate light and dark defaults.

## Installation

Download the archive for your OS and architecture from [GitHub Releases](https://github.com/punassuming/daybreak/releases), unpack it, and put `daybreak` on your `PATH`. The Windows archive also contains `daybreak-tray`; on Linux, `daybreak tray` launches the tray process. Run `daybreak setup` to install the launchers and shell hook for your platform.

To build from source, install the Go version declared in `go/go.mod`:

```sh
cd go
go build -o dist/daybreak ./cmd/daybreak
```

See [go/README.md](go/README.md) for build, packaging, and release instructions.

## Commands

```text
daybreak [light|dark|toggle|select|setup|tray]
```

- `daybreak` or `daybreak toggle`: detect the current system mode and apply the opposite mode.
- `daybreak light` / `daybreak dark`: explicitly apply a mode.
- `daybreak select`: preview palettes and set the default theme for light and dark modes.
- `daybreak setup`: install shell hooks and platform launchers, then refresh generated artifacts. It does not apply a system mode.
- `daybreak tray`: run the platform tray process.
- `daybreak --help`: show CLI usage; release builds also support `daybreak --version` (source builds print `dev`).

Toggle detection uses KDE's configured `ColorScheme` on Linux and `AppsUseLightTheme` in the current user's Windows registry on Windows. Detection errors default to light, so toggle then targets dark.

## Configuration

Daybreak stores settings in `~/.config/daybreak/config.toml`; set `DAYBREAK_CONFIG_DIR` to use another directory. The file is created with defaults and migrated when Daybreak sees an older schema. The selector writes the selected light/dark theme names.

```toml
schema_version = 2

[system]
linux_kde_light = "BreathLight"
linux_kde_dark = "BreathDark"
windows_cursor_light = ""
windows_cursor_dark = ""
linux_kde_cursor_light = ""
linux_kde_cursor_dark = ""

[theme]
active = "Nord"
light = "Nord"
dark = "Nord"

[integrations]
windows_terminal_light_scheme = "One Half Light"
windows_terminal_dark_scheme = "One Half Dark"
obsidian_light_theme = "moonstone"
obsidian_dark_theme = "obsidian"
neovim_light_scheme = "tokyonight-day"
neovim_dark_scheme = "tokyonight"
herdr_light_theme = "catppuccin-latte"
herdr_dark_theme = "catppuccin"
yazi_light_flavor = ""
yazi_dark_flavor = ""
claude_code_light_theme = "light"
claude_code_dark_theme = "dark"
codex_light_theme = "one-half-light"
codex_dark_theme = "one-half-dark"
```

The selected palette and selected app preset are separate settings. For example, choosing Daybreak's Nord palette does not change the Herdr preset unless `herdr_light_theme` and `herdr_dark_theme` are also changed. Optional cursor settings and Yazi flavors are blank by default.

## Generated files and shell setup

Each mode apply attempts to write Daybreak-owned state files to the config directory. These are outputs for shell configs and other tools to source or read:

| File | Purpose |
| --- | --- |
| `palette.json` | Current theme, mode, palette, semantic tokens, and accent tokens. |
| `env.sh` | Shell exports such as `DAYBREAK_THEME`, `DAYBREAK_MODE`, `DAYBREAK_COLOR_BG`, and `DAYBREAK_ACCENT_PRIMARY`. |
| `ls_colors.sh` | `LS_COLORS` entries derived from semantic colors. |
| `theme.sh`, `theme.fish`, `theme.ps1` | OSC color updates for shells opened after a mode change. |
| `theme.lua` | Current Neovim mode and colorscheme selection. |
| `nvim_bootstrap.lua`, `nvim_watcher.lua` | Neovim startup/live-reload integration helpers. |

Run `daybreak setup` to install a hook in the detected Bash, Zsh, or Fish startup file on Linux, or the active PowerShell profile on Windows. If you manage shell startup files yourself, source the appropriate `theme.*` file there. For POSIX shells, for example:

```sh
[ -f "$HOME/.config/daybreak/theme.sh" ] && . "$HOME/.config/daybreak/theme.sh"
```

Daybreak also writes `~/.local/share/color-schemes/DaybreakTheme.colors` on Linux. It is not applied by default. To use it for both modes, set `linux_kde_light = "DaybreakTheme"` and `linux_kde_dark = "DaybreakTheme"` under `[system]`.

## How a mode switch works

1. Daybreak loads and migrates its TOML configuration.
2. `toggle` detects the system mode and picks the opposite; explicit `light` and `dark` skip detection.
3. Daybreak resolves the configured theme for that mode and gets its palette, generating a paired palette when needed.
4. It asks the system adapter to apply the OS appearance.
5. It calls each platform's application adapters. These are independent and best-effort; adapter errors are logged and do not prevent other integrations from running.
6. It writes generated Daybreak artifacts. Artifact failures are logged and do not fail the mode apply.

`setup` follows a separate path: it installs hooks/launchers and refreshes generated artifacts for the detected or last-known mode without applying the system appearance.

## Limitations

- Linux system appearance support targets KDE Plasma. Other desktops may still receive terminal/app changes, but Daybreak does not apply their desktop theme.
- Linux shell hooks are generated for Bash, Zsh, and Fish. Other shells need a manual source command.
- Universal PTY broadcasts only work for terminals that accept OSC color sequences and allow the current user to write to their PTYs.
- Kitty live recoloring depends on Kitty remote control being available.
- Ghostty and WezTerm need user-installed theme source files and main-config includes. Yazi needs installed flavor packages and non-empty configured flavor names.
- Applications may need a restart or their own config reload before settings changes appear. Herdr is explicitly asked to reload; Codex documents its selected theme primarily for code and diff syntax highlighting.
- Application settings that Daybreak patches remain user-owned; Daybreak does not manage or install the referenced application themes.

## Development

Contributor workflows and implementation constraints are in [AGENTS.md](AGENTS.md). Build and release instructions are in [go/README.md](go/README.md).

## License

MIT
