//go:build linux

package shellsetup

import (
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

// InstallShellHook mirrors shell_setup.install_shell_hook for
// platform.system() == "Linux".
func InstallShellHook() {
	installLinuxDesktopEntry()
	installLinuxTrayAutostart()

	shellPath := os.Getenv("SHELL")
	if shellPath == "" {
		log.Printf("Could not detect shell (SHELL env var missing).")
		return
	}

	shellName := strings.ToLower(filepath.Base(shellPath))
	rcPath, hook := shellConfig(shellName)
	if rcPath == "" {
		log.Printf("Shell '%s' is not currently supported for auto-setup.", shellName)
		log.Printf("Please manually add the source command to your shell configuration.")
		return
	}

	writeHook(rcPath, hook, shellName)
}

func shellConfig(shellName string) (rcPath, hook string) {
	home, err := os.UserHomeDir()
	if err != nil {
		home = "."
	}

	switch {
	case strings.Contains(shellName, "bash"):
		return filepath.Join(home, ".bashrc"),
			"\n# Daybreak Theme Hook\n[ -f \"$HOME/.config/daybreak/theme.sh\" ] && . \"$HOME/.config/daybreak/theme.sh\"\n"
	case strings.Contains(shellName, "zsh"):
		return filepath.Join(home, ".zshrc"),
			"\n# Daybreak Theme Hook\n[ -f \"$HOME/.config/daybreak/theme.sh\" ] && . \"$HOME/.config/daybreak/theme.sh\"\n"
	case strings.Contains(shellName, "fish"):
		return filepath.Join(home, ".config", "fish", "config.fish"),
			"\n# Daybreak Theme Hook\nif test -f \"$HOME/.config/daybreak/theme.fish\"\n    source \"$HOME/.config/daybreak/theme.fish\"\nend\n"
	default:
		return "", ""
	}
}

func getLinuxApplicationsDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".local", "share", "applications")
}

// buildDaybreakCommand mirrors _build_daybreak_command's POSIX branch
// (shlex.join): prefer daybreak-tray when preferGUI, else daybreak plus
// args, falling back to this running executable's own path.
func buildDaybreakCommand(preferGUI bool, args ...string) string {
	var parts []string

	if preferGUI {
		if guiExe := lookPathAny("daybreak-tray"); guiExe != "" {
			parts = []string{guiExe}
		}
	}

	if parts == nil {
		if exe := lookPathAny("daybreak"); exe != "" {
			parts = append([]string{exe}, args...)
		} else if self, err := os.Executable(); err == nil {
			parts = append([]string{self}, args...)
		}
	}

	quoted := make([]string, len(parts))
	for i, p := range parts {
		quoted[i] = shlexQuote(p)
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

var shlexSafeRE = regexp.MustCompile(`^[a-zA-Z0-9_@%+=:,./-]+$`)

// shlexQuote mirrors Python's shlex.quote.
func shlexQuote(s string) string {
	if s == "" {
		return "''"
	}
	if shlexSafeRE.MatchString(s) {
		return s
	}
	return "'" + strings.ReplaceAll(s, "'", `'"'"'`) + "'"
}

func installLinuxDesktopEntry() {
	applicationsDir := getLinuxApplicationsDir()
	if err := os.MkdirAll(applicationsDir, 0o755); err != nil {
		log.Printf("Failed to install Daybreak desktop launcher: %v", err)
		return
	}
	desktopFile := filepath.Join(applicationsDir, "daybreak.desktop")
	command := buildDaybreakCommand(false)

	lines := []string{
		"[Desktop Entry]",
		"Name=Daybreak",
		"Comment=Toggle System & Terminal Theme",
		"Exec=" + command + " toggle",
		"Icon=preferences-desktop-display-color",
		"Type=Application",
		"Categories=Utility;System;",
		"Terminal=false",
		"Actions=Light;Dark;Select;",
		"",
		"[Desktop Action Light]",
		"Name=Switch to Light",
		"Exec=" + command + " light",
		"Icon=weather-clear",
		"",
		"[Desktop Action Dark]",
		"Name=Switch to Dark",
		"Exec=" + command + " dark",
		"Icon=weather-clear-night",
		"",
		"[Desktop Action Select]",
		"Name=Select Theme...",
		"Exec=" + command + " select",
		"Icon=preferences-desktop-theme",
		"Terminal=true",
		"",
	}

	if err := os.WriteFile(desktopFile, []byte(strings.Join(lines, "\n")), 0o644); err != nil {
		log.Printf("Failed to install Daybreak desktop launcher: %v", err)
		return
	}
	makeExecutable(desktopFile)
	log.Printf("Installed Daybreak desktop launcher at %s", desktopFile)
}

func installLinuxTrayAutostart() {
	home, _ := os.UserHomeDir()
	autostartDir := filepath.Join(home, ".config", "autostart")
	if err := os.MkdirAll(autostartDir, 0o755); err != nil {
		log.Printf("Failed to install Daybreak tray autostart: %v", err)
		return
	}
	desktopFile := filepath.Join(autostartDir, "daybreak-tray.desktop")
	command := buildDaybreakCommand(false, "tray")

	lines := []string{
		"[Desktop Entry]",
		"Name=Daybreak Tray",
		"Comment=Daybreak theme-switcher system tray icon",
		"Exec=" + command,
		"Icon=preferences-desktop-display-color",
		"Type=Application",
		"Categories=Utility;System;",
		"Terminal=false",
		"X-KDE-autostart-after=panel",
		"X-KDE-StartupNotify=false",
		"X-GNOME-Autostart-enabled=true",
		"Hidden=false",
		"",
	}

	if err := os.WriteFile(desktopFile, []byte(strings.Join(lines, "\n")), 0o644); err != nil {
		log.Printf("Failed to install Daybreak tray autostart: %v", err)
		return
	}
	makeExecutable(desktopFile)
	log.Printf("Installed Daybreak tray autostart at %s", desktopFile)
}

func makeExecutable(path string) {
	info, err := os.Stat(path)
	if err != nil {
		return
	}
	_ = os.Chmod(path, info.Mode()|0o100)
}
