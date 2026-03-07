# Daybreak 🌅

Daybreak is a cross-platform CLI tool designed to toggle system and terminal themes instantly. It provides a unified interface to switch between Light and Dark modes across your entire OS environment, including the desktop environment (KDE Plasma), terminal emulators (Kitty, Ghostty, WezTerm, Konsole, etc.), editors (Neovim), and shell sessions.

## Agent Guidance

For contributor and agent implementation rules, see `AGENTS.md` in the repository root.

## Features

- **System Integration:**
    - **KDE Plasma 6:** Toggles "Colors" and "Plasma Styles" independently, preserving your window decorations and layout.  Generates a `DaybreakTheme.colors` colorscheme file (with accent colors derived from the active palette) that users can optionally adopt via `linux_kde_light/dark` config keys.
    - **Windows 11:** Toggles System and App theme registry keys and broadcasts changes.
- **Universal Terminal Support:**
    - Instantly recolors *all* open terminal windows using OSC escape sequences (works with any xterm-compatible terminal).
    - **256-Color Extended Palette:** Automatically generates richer background/foreground nuances (indices 16-21) for sophisticated TUI elements.
- **Theme Engine:**
    - **Built-in Library:** Includes Nord, Gruvbox, Dracula, Solarized, Catppuccin, Tokyo Night, Monokai, and One Dark.
    - **Algorithmic Contrast:** Automatically generates high-contrast Light modes for dark-only themes (like Monokai/Dracula) using WCAG luminance calculations.
    - **Accent Tokens:** Derives semantic accent colors (primary, secondary, success, warning, error, selection) from every palette using the same contrast utilities.
- **Shared Theme State:**
    - Daybreak publishes its current theme to `~/.config/daybreak/` after every mode switch.  See [Generated Artifacts](#generated-artifacts) below.
- **Interactive Selector:**
    - Live split-screen preview of themes.
    - Independent defaults for Light and Dark modes.
    - Visual mocks for Code, Diff, and Status Bars to verify contrast.
- **Persistence:**
    - Automatically generates startup scripts for Bash, Zsh, Fish, and PowerShell so new terminals match the active theme.
- **No-Terminal Launchers:**
    - Installs a Linux desktop launcher so KDE users can toggle Daybreak from the app menu or a pinned panel item.
    - Installs a Windows tray launcher with a live tooltip and light/dark/toggle actions.

## Installation

### Prerequisites
- Python 3.7+
- Linux (KDE Plasma recommended) or Windows 10/11

### Install via pip (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/daybreak.git
cd daybreak

# Install in a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install .

# Or install globally using pipx
pipx install .

# Automatically install shell hooks for Bash, Zsh, Fish, or PowerShell
daybreak setup
```

## Usage

### Basic Commands

```bash
# Toggle between Light and Dark mode
daybreak toggle

# Force specific mode
daybreak dark
daybreak light

# Open the Interactive Theme Selector
daybreak select

# Re-install or fix shell hooks
daybreak setup

# Run the Windows tray icon directly
daybreak tray
```

### Desktop & Tray Usage

- **Linux (KDE-first):** `daybreak setup` now installs `~/.local/share/applications/daybreak.desktop`, so you can launch Daybreak from your application launcher, pin it to the panel, and use the Light/Dark quick actions without opening a terminal.
- **Windows:** `daybreak setup` now installs hidden tray launchers in your Start Menu and Startup folder. The tray tooltip shows the current mode, double-click toggles light/dark, and right-click opens a menu with **Toggle**, **Light**, **Dark**, and **Exit**.
- **Direct tray launch:** Windows installs also expose a `daybreak-tray` GUI entry point for launching the tray icon without a console window.

### Interactive Selector Controls
- **UP/DOWN:** Navigate themes.
- **TAB:** Toggle preview between Light/Dark.
- **SPACE:** Set the currently previewed theme as the default for that mode.
- **ENTER:** Save changes and exit.
- **q:** Quit without saving.

## Shell Integration

To ensure new terminal windows pick up the active theme, add the following to your shell configuration:

**Bash / Zsh (`~/.bashrc` or `~/.zshrc`):**
```bash
[ -f "$HOME/.config/daybreak/theme.sh" ] && . "$HOME/.config/daybreak/theme.sh"
```

**Fish (`~/.config/fish/config.fish`):**
```fish
if test -f "$HOME/.config/daybreak/theme.fish"
    source "$HOME/.config/daybreak/theme.fish"
end
```

**PowerShell (`$PROFILE`):**
```powershell
if (Test-Path "$HOME/.config/daybreak/theme.ps1") {
    . "$HOME/.config/daybreak/theme.ps1"
}
```

## Generated Artifacts

Every time Daybreak applies a theme it writes machine-readable state files to `~/.config/daybreak/`.  These files are **Daybreak-owned** — they represent Daybreak's current state and are safe for other tools or dotfiles to consume voluntarily.  Daybreak does **not** edit arbitrary third-party application config files.

| File | Description |
|------|-------------|
| `palette.json` | Full palette, semantic tokens, and accent tokens in JSON |
| `env.sh` | POSIX shell exports for `DAYBREAK_*` theme variables |
| `ls_colors.sh` | `LS_COLORS` export derived from the active theme |

### Example: sourcing theme variables

```bash
# ~/.bashrc or ~/.zshrc
[ -f "$HOME/.config/daybreak/env.sh" ] && . "$HOME/.config/daybreak/env.sh"
[ -f "$HOME/.config/daybreak/ls_colors.sh" ] && . "$HOME/.config/daybreak/ls_colors.sh"
```

This gives you variables such as `DAYBREAK_THEME`, `DAYBREAK_MODE`, `DAYBREAK_ACCENT_PRIMARY`, `DAYBREAK_COLOR_BG`, etc. that you can reference in your own scripts or prompt customisations.

### KDE Accent Colorscheme

On Linux, Daybreak also writes `~/.local/share/color-schemes/DaybreakTheme.colors` — a standard KDE INI colorscheme with accent colors derived from the active palette.  It is **not applied automatically**; to use it, set the following in `~/.config/daybreak/config.toml`:

```toml
[system]
linux_kde_light = "DaybreakTheme"
linux_kde_dark  = "DaybreakTheme"
```

Then run `daybreak light` or `daybreak dark` to apply the generated scheme.

## Neovim Integration

Add this to your `init.lua` to automatically sync Neovim's background with Daybreak:

```lua
dofile(os.getenv("HOME") .. "/.config/daybreak/nvim_watcher.lua")
```

## Configuration

Configuration is stored in `~/.config/daybreak/config.toml`. You can edit this manually or use `daybreak select`.

```toml
[system]
# KDE Color Schemes (found in /usr/share/color-schemes/)
linux_kde_light = "BreathLight"
linux_kde_dark = "BreathDark"

[terminal]
# Separate defaults for Light and Dark modes
theme_light = "Catppuccin"
theme_dark = "Nord"
```

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Submit a Pull Request.

## License

MIT
