# Daybreak Agent Guide

This file is the single source of truth for contributor and agent workflows in this repository.

## Scope
- Deliver reliable system + terminal light/dark switching.
- Keep implementation structured for future custom theme coloring.
- Maintain compatibility for current CLI commands.

## Repository Map
- `daybreak/src/daybreak/cli/main.py`: CLI command entry (`toggle|light|dark|select|setup`).
- `daybreak/src/daybreak/cli/runtime.py`: OS runtime wiring into the orchestrator.
- `daybreak/src/daybreak/core/orchestrator.py`: unified apply/toggle pipeline.
- `daybreak/src/daybreak/core/theme_registry.py`: theme lookup and mode resolution.
- `daybreak/src/daybreak/core/theme_transform.py`: semantic token conversion + contrast-safe token normalization.
- `daybreak/src/daybreak/core/theme_model.py`: token schema and validation.
- `daybreak/src/daybreak/adapters/system/kde.py`: KDE system-mode application.
- `daybreak/src/daybreak/adapters/system/windows.py`: Windows registry + broadcast mode application.
- `daybreak/src/daybreak/adapters/terminal/wrappers.py`: terminal adapter wrappers.
- `daybreak/src/daybreak/adapters/terminal/builders.py`: Linux terminal adapter set.
- `daybreak/src/daybreak/config.py`: schema-managed config loader and migration.
- `daybreak/src/daybreak/themes.py`: built-in palette definitions + palette enrichment.
- `daybreak/src/daybreak/colors.py`: luminance, contrast, and generation utilities.
- `daybreak/src/daybreak/interactive.py`: curses selector UI.
- `daybreak/src/daybreak/shell_setup.py`: shell hook setup for persistence scripts.

## Source-of-Truth Rules
- `core/*` defines orchestrated behavior and theme data contracts.
- `adapters/*` define platform/integration side effects.
- `config.py` owns persisted schema and migration from legacy config layouts.
- `themes.py` remains the built-in palette library; semantic tokens are derived from palettes.

## Implementation Rules
- Treat Linux support in this codebase as KDE-first unless explicitly expanded.
- Keep KDE changes surgical (`plasma-apply-colorscheme`, `plasma-apply-desktoptheme`, fallback writes only).
- Keep Windows changes limited to documented theme registry keys and broadcast.
- Preserve contrast behavior by using `colors.py` utilities instead of hand-tuned per-theme edits.
- Avoid claiming support for integrations that are placeholder-only.

## Common Workflows

### Add a Theme
1. Add base palette(s) in `daybreak/src/daybreak/themes.py` under `THEME_LIBRARY`.
2. Provide at least one mode; allow generation for missing paired mode.
3. Validate output through `ThemeRegistry.get_tokens(...)` and interactive preview.

### Add or Update a System Adapter
1. Implement adapter in `daybreak/src/daybreak/adapters/system/`.
2. Keep detection (`get_current_mode`) and application (`set_mode`) deterministic.
3. Wire adapter in `daybreak/src/daybreak/cli/runtime.py`.

### Add or Update a Terminal Adapter
1. Implement integration in `daybreak/src/daybreak/terminals/` if new terminal-specific logic is needed.
2. Wrap with adapter in `daybreak/src/daybreak/adapters/terminal/wrappers.py` or builders.
3. Ensure failures in one terminal do not abort overall orchestration.

### Update Interactive Selector
1. Keep the UI resilient to small terminal sizes and color capability variance.
2. Persist only through `ConfigManager` APIs (`set_mode_themes`) to preserve schema guarantees.

## Verification Checklist
- `daybreak toggle`
- `daybreak light`
- `daybreak dark`
- `daybreak select`
- `daybreak setup`
- `python -m unittest discover -s daybreak/tests`

## Known Limitations
- Linux behavior is focused on KDE.
- Some terminal integrations are best-effort or rely on user-side include/reload configuration.
- No external CI is configured in this repository yet.

## Maintenance Contract
Update this file whenever any of the following changes:
- CLI command set or command semantics.
- Config schema keys or migration behavior.
- Core/adapters module paths.
- Platform/terminal adapter support matrix.
