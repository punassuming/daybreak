//go:build windows

// Package tray ports windows_tray.py: a dependency-free Win32 system tray
// icon built directly on user32/shell32/gdi32 syscalls (no systray
// library), matching the Python original's approach of hand-rolled ctypes
// bindings rather than pulling in a third-party tray package.
package tray

import (
	"fmt"
	"log"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"

	"daybreak/internal/orchestrator"
	"daybreak/internal/shellsetup"
)

const (
	wmApp               = 0x8000
	trayCallbackMessage = wmApp + 1
)

// Controller mirrors windows_tray.py's TrayController.
type Controller struct {
	Orch         *orchestrator.Orchestrator
	CurrentMode  string
	CurrentTheme string
}

func NewController(orch *orchestrator.Orchestrator) *Controller {
	c := &Controller{Orch: orch}
	c.CurrentMode = orch.GetCurrentMode()
	c.CurrentTheme = orch.Config.GetModeThemeName(c.CurrentMode)
	return c
}

func titleCase(s string) string {
	if s == "" {
		return s
	}
	return strings.ToUpper(s[:1]) + s[1:]
}

func (c *Controller) TooltipText() string {
	return fmt.Sprintf("Daybreak (%s: %s)", titleCase(c.CurrentMode), c.CurrentTheme)
}

func (c *Controller) StatusText() string {
	return fmt.Sprintf("%s mode - %s", titleCase(c.CurrentMode), c.CurrentTheme)
}

func (c *Controller) ApplyMode(mode string) string {
	themeName, err := c.Orch.Apply(mode, "")
	if err != nil {
		log.Printf("Failed to apply %s mode: %v", mode, err)
		return c.CurrentTheme
	}
	c.CurrentMode = mode
	c.CurrentTheme = themeName
	log.Printf("Switched to %s mode using theme '%s'.", mode, themeName)
	return themeName
}

func (c *Controller) ToggleMode() (string, string) {
	mode, themeName, err := c.Orch.ApplyToggle("")
	if err != nil {
		log.Printf("Failed to toggle mode: %v", err)
		return c.CurrentMode, c.CurrentTheme
	}
	c.CurrentMode = mode
	c.CurrentTheme = themeName
	log.Printf("Switched to %s mode using theme '%s'.", mode, themeName)
	return mode, themeName
}

func (c *Controller) OpenConfig() {
	c.Orch.Config.Save()
	shellExecuteOpen(c.Orch.Config.ConfigFile)
}

func (c *Controller) RunSetup() {
	shellsetup.InstallShellHook()
}

// HandleCommand mirrors TrayController.handle_command; false means exit.
func (c *Controller) HandleCommand(id int) bool {
	switch id {
	case idToggle:
		c.ToggleMode()
	case idLight:
		c.ApplyMode("light")
	case idDark:
		c.ApplyMode("dark")
	case idOpenConfig:
		c.OpenConfig()
	case idRunSetup:
		c.RunSetup()
	case idExit:
		return false
	}
	return true
}

func shellExecuteOpen(path string) {
	shell32 := windows.NewLazySystemDLL("shell32.dll")
	shellExecuteW := shell32.NewProc("ShellExecuteW")
	p, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return
	}
	verb, _ := windows.UTF16PtrFromString("open")
	shellExecuteW.Call(0, uintptr(unsafe.Pointer(verb)), uintptr(unsafe.Pointer(p)), 0, 0, 1)
}

// renderModeIconPixels now lives in icon.go (shared with the Linux tray).
