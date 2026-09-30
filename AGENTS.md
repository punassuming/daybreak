# Daybreak Agent Guide

This file is the source of truth for contributor workflows in this repository.

## Scope

- Deliver reliable system and terminal light/dark switching.
- Keep the Go implementation structured for future custom theme coloring.
- Maintain the `daybreak` CLI command interface: `toggle|light|dark|select|setup|tray`.

## Repository Map

- `go/cmd/daybreak`: CLI entry point.
- `go/cmd/daybreak-tray`: tray-only executable.
- `go/internal/runtime`: platform runtime wiring.
- `go/internal/orchestrator`: unified apply/toggle pipeline.
- `go/internal/theme`: theme lookup, palettes, semantic tokens, and color utilities.
- `go/internal/config`: persisted config schema and migration.
- `go/internal/artifacts`: generates Daybreak-owned shared theme artifacts.
- `go/internal/adapters/system`: KDE and Windows system-mode application.
- `go/internal/adapters/terminal`: terminal integration adapters.
- `go/internal/shellsetup`: shell hooks, launchers, and generated support files.
- `go/internal/tray`: Windows and Linux tray implementations.
- `go/.goreleaser.yaml`: cross-platform release build configuration.
- `.github/workflows/release.yml`: tag-triggered GitHub release workflow.
- `README.md`: user-facing commands, configuration, integrations, and behavior.

## Source-of-Truth Rules

- `go/internal/*` defines runtime behavior and data contracts.
- `go/internal/adapters/*` define platform and integration side effects.
- Config schema and migration belong in `go/internal/config`.
- Built-in palettes belong in `go/internal/theme`.
- Daybreak publishes shared theme state through generated artifacts in its config directory. Application adapters may patch documented settings or active colors in an installed app, but should avoid taking ownership of complete user preference files or overwriting unrelated choices.

## Implementation Rules

- Treat Linux support as KDE-first unless explicitly expanded.
- Keep KDE changes surgical (`plasma-apply-colorscheme`, `plasma-apply-desktoptheme`, fallback writes only).
- Keep Windows changes limited to documented theme registry keys and broadcast.
- Preserve contrast behavior using the existing color utilities.
- Avoid claiming support for integrations that are placeholder-only.
- Artifact generation failures must be logged and must never abort the apply pipeline.
- System adapters accept an optional palette in `set_mode(mode, palette)`; adapters that do not need it may ignore it.
- `daybreak setup` installs platform hooks/launchers and refreshes generated artifacts without forcing a full mode apply.
- Keep release builds aligned with `go/go.mod` and `.goreleaser.yaml`.

## Current Integration Matrix

- Windows system: current-user light/dark registry values and a settings-change broadcast; optional saved cursor scheme.
- Linux system: KDE Plasma color scheme and Breath desktop style; optional KDE cursor theme. Linux desktop support is KDE-first.
- Linux terminals/tools: Kitty remote-control colors, writable-PTY OSC broadcast and shell hooks, Konsole, configured Ghostty/WezTerm theme files, Neovim bootstrap/watcher, Herdr, opt-in Yazi flavors, Claude Code, and Codex CLI.
- Windows terminals/tools: Windows Terminal, global Obsidian default theme, Herdr, opt-in Yazi flavors, Claude Code, and Codex CLI.
- Tray: native Windows tray and Linux StatusNotifierItem over session D-Bus.
- Custom theme presets: Nord, Gruvbox, Dracula, Solarized, Catppuccin, Tokyo Night, Monokai, and One Dark.
- Application adapters are best-effort. Document any external config include, installed theme/flavor, remote-control setting, reload, or UI limitation alongside the integration.

## Common Workflows

### Add a Theme

1. Add palette data in `go/internal/theme/library.go`.
2. Provide at least one mode and allow generation for a missing paired mode.
3. Validate output through the theme registry and selector preview.

### Add or Update an Adapter

1. Implement the adapter under `go/internal/adapters/` or the relevant platform package.
2. Keep detection and application deterministic.
3. Wire the adapter into `go/internal/runtime`.
4. Ensure failures in one terminal do not abort orchestration.

## Verification Checklist

- `cd go && go build ./...`
- `cd go && go test ./...`
- Exercise `daybreak toggle|light|dark|select|setup|tray` on supported platforms.
- Push a `v*` tag to create GitHub release binaries through GoReleaser.

## Known Limitations

- Linux system appearance is KDE-focused; the tray and application adapters still depend on the relevant desktop/session/app environment. User-confirmed manual checks cover the KDE tray, Kitty, and Herdr; this does not imply every Linux adapter is verified.
- Some integrations require user-installed themes, source files, config includes, Kitty remote control, or opt-in flavor names.
- The generated KDE `DaybreakTheme.colors` file is not selected automatically; configure `linux_kde_light` / `linux_kde_dark` to use it.
- Codex's selected `tui.theme` does not promise that every TUI surface, including the prompt composer, changes appearance.

## Maintenance Contract

Update this file whenever the CLI commands or semantics, config schema or migration, core module paths, or supported platform/integration matrix change.
