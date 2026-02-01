# Daybreak Repository Guide for Agents

This document describes the architecture, key components, and interaction guidelines for AI agents working on the `daybreak` repository.

## Project Overview
**Daybreak** is a Python-based CLI tool for toggling system and terminal themes. It emphasizes speed, universality (via OSC sequences), and visual fidelity (algorithmic contrast adjustment).

### Key Directories
- `src/daybreak/main.py`: Entry point. Handles CLI argument parsing (`toggle`, `light`, `dark`, `select`).
- `src/daybreak/platforms/`: OS-specific logic.
    - `linux_kde.py`: Handles KDE Plasma interactions (Color Scheme, Plasma Style, Window Dec). **Note:** Uses `plasma-apply-colorscheme` and direct config writing to avoid global theme resets.
    - `windows.py`: Handles Windows Registry and `WM_SETTINGCHANGE` broadcasting.
- `src/daybreak/terminals/`: Terminal emulator handlers.
    - `universal.py`: **Core Component.** Broadcasts OSC 4/10/11 sequences to all open PTYs (`/dev/pts/*`). Handles theme lookup and persistence script generation.
    - `kitty.py`, `ghostty.py`, `wezterm.py`: Specific config file swappers (secondary to UniversalPty).
- `src/daybreak/themes.py`: Theme definitions (Nord, Dracula, etc.) and auto-generation logic for missing variants.
- `src/daybreak/colors.py`: Color manipulation logic. Contains `generate_light_from_dark` and `adjust_color_for_contrast` (WCAG algorithms).
- `src/daybreak/interactive.py`: The Curses-based UI for `daybreak select`.

## Architecture Principles

1.  **Universal First:** We prioritize the `UniversalPty` broadcaster. It works on almost any terminal without configuration. Specific terminal handlers are fallbacks or for persistence.
2.  **Surgical System Changes:** On Linux/KDE, we strictly avoid "Global Themes" (`lookandfeeltool`). We modify components individually (Colors, Style) to preserve user layouts.
3.  **Algorithmic Safety:** When generating themes, strictly enforce contrast ratios. See `colors.py`.
4.  **State Management:** User preferences are stored in `~/.config/daybreak/config.toml`. State (current mode) is implied by the system's current state (we query KDE/Windows registry to decide if we are toggling to Light or Dark).

## Interaction Guidelines for Agents

### 1. Adding a New Theme
- Add the dictionary to `src/daybreak/themes.py` in `THEME_LIBRARY`.
- Define at least one mode (`dark` or `light`). The other will be auto-generated.
- **Do not** manually calculate contrast; rely on `colors.py`.

### 2. Adding a New Platform
- Create `src/daybreak/platforms/your_os.py`.
- Inherit from `PlatformHandler`.
- Implement `get_current_mode()` and `set_mode()`.
- Register it in `src/daybreak/main.py`.

### 3. Debugging Terminal Colors
- If a user reports "invisible text":
    - Check `src/daybreak/colors.py`.
    - Tweaking `adjust_color_for_contrast` parameters (min_ratio) is usually the fix.
    - Specifically check for Yellow/White text on Light Backgrounds.

### 4. modifying the Interactive UI
- Located in `src/daybreak/interactive.py`.
- Uses standard Python `curses`.
- Always wrap logic in `try/except` to prevent crashing the terminal on resize or unsupported capabilities.

### 5. Shell Persistence
- If adding a new shell (e.g., NuShell):
    - Update `UniversalPty._write_shell_script` in `src/daybreak/terminals/universal.py`.

## Common Commands for Testing
```bash
# Reinstall to apply changes
pip install .

# Test Toggle
daybreak toggle

# Test Selector (Requires large terminal window)
daybreak select
```
