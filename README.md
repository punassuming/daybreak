# Daybreak 🌅

Daybreak is a cross-platform CLI tool to toggle system and application themes (Light/Dark) instantly.

## Features

- **System:** Toggles KDE Plasma 6 Global Theme and Windows 11 System/App Theme.
- **Terminals:** 
    - **Universal:** Instantly recolors *all* open terminal windows (Any libvte/xterm compatible terminal) using OSC escape codes.
    - **Nord Theme:** Defaults to the beautiful Nord color palette.
    - **Specific Support:** Kitty, Ghostty, WezTerm, Konsole.
- **Editors:** 
    - **Neovim:** Syncs `background` setting via RPC or config file.
- **Browsers:** Logs support for Firefox/Chrome (via system sync).

## Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/daybreak.git
cd daybreak

# Install (Recommended: use venv)
python3 -m venv venv
source venv/bin/activate
pip install .
```

## Usage

```bash
daybreak toggle   # Switch between Light and Dark
daybreak dark     # Force Dark Mode
daybreak light    # Force Light Mode
```

### Persistence
To ensure new terminals pick up the active theme, add this to your shell config (`.bashrc` / `.zshrc`):

```bash
[ -f "$HOME/.config/daybreak/theme.sh" ] && . "$HOME/.config/daybreak/theme.sh"
```

### Neovim Integration
Add this to your `init.lua`:

```lua
dofile(os.getenv("HOME") .. "/.config/daybreak/nvim_watcher.lua")
```
