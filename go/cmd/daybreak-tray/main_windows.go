//go:build windows

// Command daybreak-tray is the GUI-subsystem entry point mirroring
// pyproject.toml's `daybreak-tray = "daybreak.windows_tray:run_windows_tray"`
// gui_scripts entry: launches the tray icon directly with no console
// window. Built with `-ldflags="-H=windowsgui"` (see .goreleaser.yaml) so
// double-clicking it, or the setup-installed Startup .vbs launcher running
// it, never flashes a console.
package main

import (
	"fmt"
	"os"

	"daybreak/internal/config"
	"daybreak/internal/runtime"
	"daybreak/internal/tray"
)

func main() {
	cfg := config.NewManager("")
	orch := runtime.BuildOrchestrator(cfg)
	if err := tray.Run(orch); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
