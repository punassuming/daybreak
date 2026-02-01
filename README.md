# Daybreak 🌅

Daybreak is a cross-platform CLI tool designed to toggle system and terminal themes instantly. It provides a unified interface to switch between Light and Dark modes across your entire OS environment, including the desktop environment (KDE Plasma), terminal emulators (Kitty, Ghostty, WezTerm, Konsole, etc.), editors (Neovim), and shell sessions.

## Features

- **System Integration:**
    - **KDE Plasma 6:** Toggles "Colors" and "Plasma Styles" independently, preserving your window decorations and layout.
    - **Windows 11:** Toggles System and App theme registry keys and broadcasts changes.
- **Universal Terminal Support:**
    - Instantly recolors *all* open terminal windows using OSC escape sequences (works with any xterm-compatible terminal).
    - **256-Color Extended Palette:** Automatically generates richer background/foreground nuances (indices 16-21) for sophisticated TUI elements.
- **Theme Engine:**
    - **Built-in Library:** Includes Nord, Gruvbox, Dracula, Solarized, Catppuccin, Tokyo Night, Monokai, and One Dark.
    - **Algorithmic Contrast:** Automatically generates high-contrast Light modes for dark-only themes (like Monokai/Dracula) using WCAG luminance calculations.
- **Interactive Selector:**
    - Live split-screen preview of themes.
    - Independent defaults for Light and Dark modes.
    - Visual mocks for Code, Diff, and Status Bars to verify contrast.
- **Persistence:**
    - Automatically generates startup scripts for Bash, Zsh, Fish, and PowerShell so new terminals match the active theme.

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
```

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