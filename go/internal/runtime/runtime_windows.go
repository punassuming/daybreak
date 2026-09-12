//go:build windows

// Package runtime ports cli/runtime.py's build_orchestrator: OS-specific
// wiring of the system adapter (and, from phase 4 on, terminal adapters)
// into a ready-to-use Orchestrator.
package runtime

import (
	"daybreak/internal/adapters/system"
	"daybreak/internal/adapters/terminal"
	"daybreak/internal/artifacts"
	"daybreak/internal/config"
	"daybreak/internal/orchestrator"
	"daybreak/internal/theme"
)

// BuildOrchestrator mirrors build_orchestrator() for os_name == "Windows".
func BuildOrchestrator(cfg *config.Manager) *orchestrator.Orchestrator {
	return &orchestrator.Orchestrator{
		Config:            cfg,
		SystemAdapter:     system.WindowsAdapter{Config: cfg},
		TerminalAdapters:  terminal.BuildWindowsTerminalAdapters(cfg),
		Registry:          theme.NewRegistry(),
		GenerateArtifacts: artifacts.Generate,
	}
}
