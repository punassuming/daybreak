//go:build linux

package main

import (
	"daybreak/internal/orchestrator"
	"daybreak/internal/tray"
)

func runTray(orch *orchestrator.Orchestrator) error {
	return tray.Run(orch)
}
