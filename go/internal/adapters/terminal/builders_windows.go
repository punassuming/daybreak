//go:build windows

package terminal

import (
	"daybreak/internal/config"
	"daybreak/internal/orchestrator"
)

// BuildWindowsTerminalAdapters mirrors adapters/terminal/builders.py's
// build_windows_terminal_adapters.
//
// ObsidianAdapter was previously implemented but never wired into either
// the Python or Go builder (dead code in both) — fixed on both sides now.
func BuildWindowsTerminalAdapters(cfg *config.Manager) []orchestrator.TerminalAdapter {
	return []orchestrator.TerminalAdapter{
		WindowsTerminalAdapter{Config: cfg},
		ObsidianAdapter{Config: cfg},
		HerdrAdapter{Config: cfg},
		YaziAdapter{Config: cfg},
		ClaudeCodeAdapter{Config: cfg},
		CodexAdapter{Config: cfg},
	}
}
