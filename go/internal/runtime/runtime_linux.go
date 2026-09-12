//go:build linux

package runtime

import (
	"daybreak/internal/adapters/system"
	"daybreak/internal/adapters/terminal"
	"daybreak/internal/artifacts"
	"daybreak/internal/config"
	"daybreak/internal/orchestrator"
	"daybreak/internal/theme"
)

// BuildOrchestrator mirrors build_orchestrator() for os_name == "Linux"
// (KDE-first, per AGENTS.md).
func BuildOrchestrator(cfg *config.Manager) *orchestrator.Orchestrator {
	return &orchestrator.Orchestrator{
		Config:            cfg,
		SystemAdapter:     system.KDEAdapter{Config: cfg},
		TerminalAdapters:  terminal.BuildLinuxTerminalAdapters(cfg),
		Registry:          theme.NewRegistry(),
		GenerateArtifacts: artifacts.Generate,
	}
}
