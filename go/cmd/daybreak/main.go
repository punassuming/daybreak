// Command daybreak ports cli/main.py: the `daybreak <mode>` CLI surface
// (toggle/light/dark/select/setup/tray).
package main

import (
	"fmt"
	"log"
	"os"

	"github.com/spf13/cobra"

	"daybreak/internal/config"
	"daybreak/internal/runtime"
	"daybreak/internal/selector"
	"daybreak/internal/shellsetup"
)

func main() {
	log.SetFlags(0)

	root := &cobra.Command{
		Use:   "daybreak [light|dark|toggle|select|setup|tray]",
		Short: "Daybreak: Toggle system and application themes.",
		Args:  cobra.MaximumNArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			mode := "toggle"
			if len(args) == 1 {
				mode = args[0]
			}
			return run(mode)
		},
	}

	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run(mode string) error {
	switch mode {
	case "select":
		cfg := config.NewManager("")
		return selector.Run(cfg)
	case "setup":
		cfg := config.NewManager("")
		orch := runtime.BuildOrchestrator(cfg)
		shellsetup.InstallShellHook()
		shellsetup.RefreshGeneratedArtifacts(orch)
		return nil
	case "tray":
		cfg := config.NewManager("")
		orch := runtime.BuildOrchestrator(cfg)
		return runTray(orch)
	case "light", "dark", "toggle":
		cfg := config.NewManager("")
		orch := runtime.BuildOrchestrator(cfg)

		if mode == "toggle" {
			targetMode, themeName, err := orch.ApplyToggle("")
			if err != nil {
				return err
			}
			log.Printf("Switched to %s mode using theme '%s'.", targetMode, themeName)
			return nil
		}

		themeName, err := orch.Apply(mode, "")
		if err != nil {
			return err
		}
		log.Printf("Switched to %s mode using theme '%s'.", mode, themeName)
		return nil
	default:
		return fmt.Errorf("unknown mode %q: expected one of light, dark, toggle, select, setup, tray", mode)
	}
}
