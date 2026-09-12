//go:build windows

package shellsetup

import (
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

// InstallShellHook mirrors shell_setup.install_shell_hook for
// platform.system() == "Windows".
func InstallShellHook() {
	installPowerShellHook()
	installWindowsTrayLauncher()
}

// Query pwsh (PowerShell 7+) before Windows PowerShell 5.1's `powershell`:
// on a machine with both installed, pwsh is virtually always the one the
// user actually runs, and hooking the one nobody launches silently no-ops
// setup. This intentionally diverges from the Python original, which
// queries `powershell` first.
func installPowerShellHook() {
	profilePathStr := queryPowerShellProfilePath("pwsh")
	if profilePathStr == "" {
		profilePathStr = queryPowerShellProfilePath("powershell")
	}
	if profilePathStr == "" {
		log.Printf("Could not determine PowerShell profile path.")
		return
	}

	hook := "\n# Daybreak Theme Hook\nif (Test-Path \"$HOME/.config/daybreak/theme.ps1\") {\n    . \"$HOME/.config/daybreak/theme.ps1\"\n}\n"
	writeHook(profilePathStr, hook, "PowerShell")
}

func queryPowerShellProfilePath(executable string) string {
	cmd := exec.Command(executable, "-NoProfile", "-Command", "Write-Host $PROFILE.CurrentUserCurrentHost")
	out, err := cmd.Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

func getWindowsProgramsDir() string {
	appData := os.Getenv("APPDATA")
	if appData == "" {
		home, _ := os.UserHomeDir()
		appData = filepath.Join(home, "AppData", "Roaming")
	}
	return filepath.Join(appData, "Microsoft", "Windows", "Start Menu", "Programs")
}

func getWindowsStartupDir() string {
	return filepath.Join(getWindowsProgramsDir(), "Startup")
}

// buildDaybreakCommand mirrors shell_setup._build_daybreak_command on
// Windows: prefer daybreak-tray(.exe) when preferGUI, else daybreak(.exe)
// plus args, falling back to this running executable's own path if neither
// is found on PATH (the Go equivalent of the Python original's "invoke the
// current interpreter as `python -m daybreak`" fallback).
func buildDaybreakCommand(preferGUI bool, args ...string) string {
	var parts []string

	if preferGUI {
		if guiExe := lookPathAny("daybreak-tray.exe", "daybreak-tray"); guiExe != "" {
			parts = []string{guiExe}
		}
	}

	if parts == nil {
		if exe := lookPathAny("daybreak.exe", "daybreak"); exe != "" {
			parts = append([]string{exe}, args...)
		} else if self, err := os.Executable(); err == nil {
			parts = append([]string{self}, args...)
		}
	}

	quoted := make([]string, len(parts))
	for i, p := range parts {
		quoted[i] = syscall.EscapeArg(p)
	}
	return strings.Join(quoted, " ")
}

func lookPathAny(names ...string) string {
	for _, name := range names {
		if path, err := exec.LookPath(name); err == nil {
			return path
		}
	}
	return ""
}

func installWindowsTrayLauncher() {
	command := buildDaybreakCommand(true, "tray")
	launcherScript := "Set shell = CreateObject(\"WScript.Shell\")\n" +
		"shell.Run \"" + strings.ReplaceAll(command, `"`, `""`) + "\", 0\n"

	programsDir := getWindowsProgramsDir()
	startupDir := getWindowsStartupDir()

	for _, dir := range []string{programsDir, startupDir} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			log.Printf("Failed to install Daybreak tray launcher: %v", err)
			return
		}
	}

	launchers := []string{
		filepath.Join(programsDir, "Daybreak Tray.vbs"),
		filepath.Join(startupDir, "Daybreak Tray.vbs"),
	}

	for _, path := range launchers {
		if err := os.WriteFile(path, []byte(launcherScript), 0o644); err != nil {
			log.Printf("Failed to install Daybreak tray launcher at %s: %v", path, err)
			continue
		}
		log.Printf("Installed Daybreak tray launcher at %s", path)
	}
}
