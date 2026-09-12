//go:build linux

package terminal

import (
	"daybreak/internal/config"
	"daybreak/internal/orchestrator"
)

// BuildLinuxTerminalAdapters mirrors adapters/terminal/builders.py's
// build_linux_terminal_adapters, plus the cross-platform CLI-tool
// integrations (herdr, yazi, Claude Code, Codex) that have no Python
// equivalent yet.
func BuildLinuxTerminalAdapters(cfg *config.Manager) []orchestrator.TerminalAdapter {
	return []orchestrator.TerminalAdapter{
		UniversalPtyAdapter{Config: cfg},
		NewNeovimAdapter(cfg),
		KittyAdapter{},
		NewGhosttyAdapter(),
		NewWezTermAdapter(),
		KonsoleAdapter{},
		HerdrAdapter{Config: cfg},
		YaziAdapter{Config: cfg},
		ClaudeCodeAdapter{Config: cfg},
		CodexAdapter{Config: cfg},
	}
}
