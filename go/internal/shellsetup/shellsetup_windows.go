//go:build windows

package shellsetup

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
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

func lookPathAny(names ...string) string {
	for _, name := range names {
		if path, err := exec.LookPath(name); err == nil {
			return path
		}
	}
	return ""
}

// resolveTrayTarget picks what the Start Menu/Startup shortcut should
// launch: the GUI-subsystem daybreak-tray.exe directly (no console, no
// arguments needed — its main() always runs the tray) when found, else a
// fallback to daybreak.exe tray (console-subsystem: briefly flashes a
// console on launch, but still works).
func resolveTrayTarget() (target string, args string) {
	if guiExe := lookPathAny("daybreak-tray.exe", "daybreak-tray"); guiExe != "" {
		return guiExe, ""
	}
	if exe := lookPathAny("daybreak.exe", "daybreak"); exe != "" {
		return exe, "tray"
	}
	if self, err := os.Executable(); err == nil {
		return self, "tray"
	}
	return "", ""
}

// installWindowsTrayLauncher creates real .lnk shortcuts (via PowerShell's
// WScript.Shell COM object — there's no pure Go stdlib way to write the
// binary .lnk format) rather than the .vbs scripts this used to write.
// A .vbs in the Start Menu always shows a generic script icon no matter
// what it launches; a .lnk shows the target's own icon (daybreak-tray.exe
// now has one — see assets/daybreak.ico / tools/genicon) and, since the
// target is GUI-subsystem, needs no "run hidden" wrapper either.
func installWindowsTrayLauncher() {
	target, args := resolveTrayTarget()
	if target == "" {
		log.Printf("Failed to install Daybreak tray launcher: daybreak-tray/daybreak not found.")
		return
	}

	programsDir := getWindowsProgramsDir()
	startupDir := getWindowsStartupDir()

	for _, dir := range []string{programsDir, startupDir} {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			log.Printf("Failed to install Daybreak tray launcher: %v", err)
			return
		}
	}

	launchers := []string{
		filepath.Join(programsDir, "Daybreak Tray.lnk"),
		filepath.Join(startupDir, "Daybreak Tray.lnk"),
	}

	// Clean up .vbs launchers from older installs so Start Menu search
	// doesn't show both the old script and the new shortcut.
	for _, dir := range []string{programsDir, startupDir} {
		_ = os.Remove(filepath.Join(dir, "Daybreak Tray.vbs"))
	}

	// A Scoop shim's own .exe carries a generic stub icon, not the real
	// app's — resolve through its companion .shim file to the actual
	// installed binary so the shortcut's icon is daybreak-tray's sun, not
	// Scoop's generic stub icon. TargetPath stays the shim itself so
	// launching still goes through PATH/Scoop's update mechanism.
	iconSource := resolveShimTarget(target)

	for _, path := range launchers {
		if err := createShortcut(path, target, args, filepath.Dir(target), iconSource); err != nil {
			log.Printf("Failed to install Daybreak tray launcher at %s: %v", path, err)
			continue
		}
		log.Printf("Installed Daybreak tray launcher at %s", path)
	}
}

var shimPathRE = regexp.MustCompile(`(?m)^\s*path\s*=\s*"([^"]+)"\s*$`)

// resolveShimTarget reads a Scoop-generated "<name>.shim" companion file
// (a plain-text `path = "C:\...\real.exe"` pointer) next to exePath, if
// one exists, and returns the real binary it points at; otherwise returns
// exePath unchanged (e.g. when it's not a Scoop shim at all).
func resolveShimTarget(exePath string) string {
	shimFile := strings.TrimSuffix(exePath, filepath.Ext(exePath)) + ".shim"
	content, err := os.ReadFile(shimFile)
	if err != nil {
		return exePath
	}
	if m := shimPathRE.FindSubmatch(content); m != nil {
		return string(m[1])
	}
	return exePath
}

// createShortcut builds a .lnk via PowerShell's WScript.Shell COM object
// (New-Object -ComObject WScript.Shell -> CreateShortcut -> Save), the
// standard way to create Windows shortcuts short of hand-writing the
// MS-SHLLINK binary format.
func createShortcut(lnkPath, target, args, workingDir, iconSource string) error {
	script := "$s = New-Object -ComObject WScript.Shell; " +
		"$sc = $s.CreateShortcut(" + psQuote(lnkPath) + "); " +
		"$sc.TargetPath = " + psQuote(target) + "; "
	if args != "" {
		script += "$sc.Arguments = " + psQuote(args) + "; "
	}
	script += "$sc.WorkingDirectory = " + psQuote(workingDir) + "; " +
		"$sc.IconLocation = " + psQuote(iconSource+",0") + "; " +
		"$sc.Save()"

	for _, exe := range []string{"pwsh", "powershell"} {
		cmd := exec.Command(exe, "-NoProfile", "-Command", script)
		if err := cmd.Run(); err == nil {
			return nil
		}
	}
	return fmt.Errorf("no working PowerShell (pwsh/powershell) found to create the shortcut")
}

// psQuote wraps a string in PowerShell single-quotes, doubling any
// embedded single quote — the escaping rule for PS single-quoted literals.
func psQuote(s string) string {
	return "'" + strings.ReplaceAll(s, "'", "''") + "'"
}
