# Daybreak Go implementation

The Go application is the maintained Daybreak implementation. Product behavior and configuration are described in the [root README](../README.md); repository conventions are in [AGENTS.md](../AGENTS.md).

## Build and verification

Use the Go version declared in `go.mod` (`go 1.27.1`). From this directory:

```sh
go build ./...                       # compile all host-platform packages
go test ./...                        # run package tests
go build -o dist/daybreak ./cmd/daybreak
```

Cross-compile release targets (CGO is disabled):

```sh
GOOS=linux GOARCH=amd64 go build -o dist/daybreak ./cmd/daybreak
GOOS=windows GOARCH=amd64 go build -o dist/daybreak.exe ./cmd/daybreak
```

The CLI reports `dev` for a source build. GoReleaser injects the tagged release version; run `daybreak --version` to display it.

## Release process

The root `.github/workflows/release.yml` runs GoReleaser on every pushed `v*` tag. It builds the CLI for Linux and Windows on amd64 and arm64, and also builds `daybreak-tray` for both architectures on both platforms. The Windows tray executable uses the GUI subsystem to avoid opening a console. GoReleaser publishes zip archives and `checksums.txt` to a GitHub Release.

For a local packaging check, install GoReleaser v2 and run:

```sh
goreleaser release --snapshot --clean --skip=publish
```

To publish, merge the release changes to `main`, create a new `vMAJOR.MINOR.PATCH` tag on that commit, and push both the branch and tag:

```sh
git tag -a vX.Y.Z -m "Daybreak vX.Y.Z"
git push origin main
git push origin vX.Y.Z
```

Then check the Actions run and the GitHub Release for all platform archives and checksums. The release workflow uses the repository's `GITHUB_TOKEN`; no local token is needed.

## Windows executable icon

The checked-in `.syso` resources embed `assets/daybreak.ico` in Windows builds. Keep these resource files in sync if the icon or executable metadata changes, and cross-compile both architectures to confirm the resources are present.

## Layout

- `cmd/daybreak` — CLI and version output.
- `cmd/daybreak-tray` — standalone tray executable.
- `internal/runtime` — platform adapter wiring.
- `internal/orchestrator` — mode detection, palette selection, and apply pipeline.
- `internal/theme` and `internal/config` — palettes, tokens, settings, and migration.
- `internal/adapters/system` and `internal/adapters/terminal` — OS and app integrations.
- `internal/artifacts` — Daybreak-owned palette and shell artifacts.
- `internal/shellsetup` — shell hooks, launchers, and setup refresh.
- `internal/selector` — interactive palette picker.
- `internal/tray` — Windows native tray and Linux D-Bus StatusNotifierItem.
