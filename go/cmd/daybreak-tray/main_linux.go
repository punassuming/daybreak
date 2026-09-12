//go:build linux

// Command daybreak-tray on Linux mirrors pyproject.toml's
// `daybreak-tray-linux = "daybreak.linux_tray:run_linux_tray"` console script.
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
