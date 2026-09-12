# Daybreak (Go build)

Go port of the Python `daybreak` CLI (`../src/daybreak`), built as a single
dependency-free binary so it can ship via Scoop instead of pip/pipx. See
the root `README.md`/`AGENTS.md` for what Daybreak does; this file only
covers building, testing, and installing *this* Go build.

## Status

- Windows: fully implemented and exercised against a real machine (theme
  toggle, Windows Terminal, Obsidian, herdr, Claude Code, Codex, yazi,
  `setup`, `select`, tray icon).
- Linux/KDE: implemented (system adapter, terminal adapters, tray) but
  **not yet verified on a real Linux/KDE machine** — this was ported
  without one available. Treat it as untested until someone runs it there.

## Prerequisites

- Go 1.27+ (`scoop install go` works fine on Windows)
- [goreleaser](https://goreleaser.com/) only if you want release-shaped
  archives (`scoop install goreleaser`); plain `go build` is enough for
  day-to-day development.

## Build

```sh
cd go
go build ./...                      # compile everything for the host OS
go build -o dist/daybreak.exe ./cmd/daybreak        # just the CLI
go build -o dist/daybreak-tray.exe ./cmd/daybreak-tray  # just the tray

# cross-compile (no CGO involved, so this always works from any host)
GOOS=windows GOARCH=amd64 go build -o dist/daybreak.exe ./cmd/daybreak
GOOS=linux   GOARCH=amd64 go build -o dist/daybreak    ./cmd/daybreak
```

## Test

```sh
go vet ./...   # ignore the "possible misuse of unsafe.Pointer" hit in
               # internal/tray/run_windows.go — that's the standard
               # MAKEINTRESOURCE(id) pattern for LoadIconW/LoadCursorW,
               # not a real bug, so don't gate on vet's exit code here.
go test ./...
```

## Release build (goreleaser)

`.goreleaser.yaml` builds `daybreak` (windows/linux × amd64/arm64) and
`daybreak-tray` (same matrix, `-H=windowsgui` on Windows so it never opens
a console), and zips each OS/arch pair together.

```sh
cd go
goreleaser release --snapshot --clean --skip=publish
# -> go/dist/daybreak_<version>_<os>_<arch>.zip, plus checksums.txt
```

`--snapshot` needs no git tag and does not publish or push anything — it's
the safe way to produce real release artifacts locally. A real
`goreleaser release --clean` (no `--snapshot`) additionally needs
`GITHUB_TOKEN` set and pushes a GitHub release for the current tag; that's
what `.github/workflows/release.yml` runs on `git push --tags`.

## App icon (Windows)

`assets/daybreak.ico` (checked in) is generated from the same pixel art
the tray icon already draws at runtime (`tray.RenderModeIconPixels`), via:

```sh
go run ./tools/genicon   # regenerate assets/daybreak.ico if the icon design changes
```

It's embedded into `daybreak.exe`/`daybreak-tray.exe` via `.syso` files
(also checked in: `cmd/daybreak/rsrc_windows_*.syso`,
`cmd/daybreak-tray/rsrc_windows_*.syso`) that `go build` links in
automatically — nothing extra needed for a normal build or for CI/goreleaser.
Regenerate them after changing the icon or version/product metadata:

```sh
go install github.com/tc-hib/go-winres@latest   # one-time
go-winres simply --arch amd64,arm64 --icon assets/daybreak.ico \
  --manifest cli --product-name Daybreak \
  --file-description "Daybreak: toggle system and terminal light/dark themes" \
  --original-filename daybreak.exe --out cmd/daybreak/rsrc
go-winres simply --arch amd64,arm64 --icon assets/daybreak.ico \
  --manifest gui --product-name Daybreak \
  --file-description "Daybreak tray icon" \
  --original-filename daybreak-tray.exe --out cmd/daybreak-tray/rsrc
```

The Start Menu/Startup shortcut (`internal/shellsetup`'s
`installWindowsTrayLauncher`) is a real `.lnk` (built via PowerShell's
`WScript.Shell` COM object — there's no pure-Go way to write the binary
.lnk format), not a `.vbs` like older installs: a `.vbs` in the Start Menu
always shows a generic script icon no matter what it launches. It also
resolves through a Scoop shim's companion `.shim` file to point the
shortcut's icon at the real installed `daybreak-tray.exe` — the shim
`.exe` itself carries a generic Scoop stub icon, not the app's.

## Installing your own build locally via Scoop

Useful for trying a build before it's ever published as a real release.
Scoop's manifest schema wants a downloadable `url` + `hash`; its
downloader (aria2) doesn't support `file://`, so the trick is to name the
zip exactly what Scoop's cache expects and let it find that instead of
downloading:

```sh
cd go
goreleaser release --snapshot --clean --skip=publish
sha256sum dist/daybreak_<version>_windows_amd64.zip   # copy this hash
```

Write a throwaway manifest (anywhere outside the repo — do **not** use
this to overwrite `bucket/daybreak.json`, which is the real manifest and
should only ever point at a real GitHub release):

```json
{
    "version": "<version>",
    "url": "file:///C:/path/to/go/dist/daybreak_<version>_windows_amd64.zip",
    "hash": "<sha256 from above>",
    "bin": ["daybreak.exe", "daybreak-tray.exe"],
    "post_install": ["& \"$dir\\daybreak.exe\" setup"]
}
```

```powershell
# Scoop's cache filename convention: <app>#<version>#<7-char-manifest-hash>.zip
# Run `scoop install <manifest.json>` once — it fails the download and
# prints the exact filename it expected in ~\scoop\cache; copy your zip
# there under that name, then run install again and it loads from cache.
Copy-Item dist\daybreak_<version>_windows_amd64.zip `
  "$env:USERPROFILE\scoop\cache\<app-name>#<version>#<manifest-hash>.zip"
scoop install path\to\your-manifest.json
```

This installs under whatever app name you picked (e.g. `daybreak-local`),
independently of any real `daybreak` install — `scoop uninstall
daybreak-local` removes it cleanly. Since `~\scoop\shims` normally
precedes `~\.local\bin` (pipx) on `PATH`, a Scoop-installed `daybreak`
shadows a pipx-installed one without needing to uninstall the latter.

## Installing a real release via Scoop

Once a tag is pushed and `bucket/daybreak.json` points at a real GitHub
release (not the placeholder hash/URL it ships with today):

```powershell
scoop bucket add daybreak https://github.com/punassuming/daybreak
scoop install daybreak/daybreak
```

## Layout

- `cmd/daybreak` — the CLI (`toggle|light|dark|select|setup|tray`)
- `cmd/daybreak-tray` — GUI-subsystem tray-only entry point (Windows: no
  console window; Linux: same tray, mirrors the Python `daybreak-tray-linux`
  console script)
- `internal/theme`, `internal/config`, `internal/orchestrator`,
  `internal/artifacts` — core engine, ported line-for-line from
  `../src/daybreak/{themes,colors,config,core}.py`
- `internal/adapters/system` — Windows registry + KDE `plasma-apply-*`,
  plus cursor-scheme switching (not in the Python original)
- `internal/adapters/terminal` — Windows Terminal, Obsidian, Kitty,
  Konsole, Ghostty, WezTerm, Neovim, universal PTY broadcast, plus four
  integrations with no Python equivalent yet: herdr, yazi, Claude Code,
  Codex CLI
- `internal/selector` — tcell-based theme picker (`daybreak select`),
  replacing curses (which doesn't work on Windows without the unlisted
  `windows-curses` dependency)
- `internal/shellsetup` — `daybreak setup`: shell hooks, Windows tray
  launchers, Linux desktop entry/autostart, generated-artifact refresh
- `internal/tray` — Windows Win32 tray (raw syscalls, no third-party tray
  library) and Linux StatusNotifierItem-over-D-Bus tray
