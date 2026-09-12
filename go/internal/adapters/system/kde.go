//go:build linux

package system

import (
	"errors"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

const kdeColorschemeName = "DaybreakTheme"

// KDEAdapter mirrors adapters/system/kde.py's KDESystemAdapter.
type KDEAdapter struct {
	Config *config.Manager
}

func (KDEAdapter) Name() string { return "kde" }

// GetCurrentMode mirrors KDESystemAdapter.get_current_mode.
func (KDEAdapter) GetCurrentMode() (string, error) {
	scheme := kreadconfig("kreadconfig6")
	if scheme == "" {
		scheme = kreadconfig("kreadconfig5")
	}
	if strings.Contains(scheme, "dark") {
		return "dark", nil
	}
	return "light", nil
}

func kreadconfig(binary string) string {
	out, err := exec.Command(binary, "--file", "kdeglobals", "--group", "General", "--key", "ColorScheme").Output()
	if err != nil {
		return ""
	}
	return strings.ToLower(strings.TrimSpace(string(out)))
}

// SetMode mirrors KDESystemAdapter.set_mode.
func (a KDEAdapter) SetMode(mode string, palette theme.Palette) {
	if palette.Colors != nil || palette.Special != nil {
		a.writeKDEColorscheme(mode, palette)
	}

	colorScheme := a.Config.GetSystemTheme("linux_kde", mode)
	cmd := exec.Command("plasma-apply-colorscheme", colorScheme)
	cmd.Stdout, cmd.Stderr = nil, nil
	if err := cmd.Run(); err != nil {
		log.Printf("Failed to apply color scheme %s", colorScheme)
	} else {
		log.Printf("Applied KDE color scheme: %s", colorScheme)
	}

	plasmaTheme := "breath-light"
	if mode == "dark" {
		plasmaTheme = "breath-dark"
	}

	desktopCmd := exec.Command("plasma-apply-desktoptheme", plasmaTheme)
	if err := desktopCmd.Run(); err != nil {
		if isNotFound(err) {
			writeCmd := exec.Command("kwriteconfig6", "--file", "plasmarc", "--group", "Theme", "--key", "name", plasmaTheme)
			if err := writeCmd.Run(); err != nil {
				log.Printf("Failed to update plasmarc: %v", err)
			} else {
				log.Printf("Set plasmarc theme to %s", plasmaTheme)
			}
		} else {
			log.Printf("Failed to apply desktop theme %s", plasmaTheme)
		}
	} else {
		log.Printf("Applied Plasma desktop theme: %s", plasmaTheme)
	}

	cursorTheme := a.Config.Data.System.LinuxKDECursorDark
	if mode == "light" {
		cursorTheme = a.Config.Data.System.LinuxKDECursorLight
	}
	if cursorTheme != "" {
		applyCursorTheme(cursorTheme)
	}
}

// applyCursorTheme mirrors the KDE side of cursor switching, not present
// in the Python original. Not applied unless linux_kde_cursor_light /
// linux_kde_cursor_dark are set (opt-in — a wrong guess would point KWin
// at a cursor theme the user hasn't installed).
func applyCursorTheme(cursorTheme string) {
	cmd := exec.Command("plasma-apply-cursortheme", cursorTheme)
	if err := cmd.Run(); err == nil {
		log.Printf("Applied KDE cursor theme: %s", cursorTheme)
		return
	} else if !isNotFound(err) {
		log.Printf("Failed to apply cursor theme %s", cursorTheme)
		return
	}

	// plasma-apply-cursortheme missing (pre-5.22): fall back to writing
	// kcminputrc directly and asking KWin to reconfigure.
	writeCmd := exec.Command("kwriteconfig6", "--file", "kcminputrc", "--group", "Mouse", "--key", "cursorTheme", cursorTheme)
	if err := writeCmd.Run(); err != nil {
		log.Printf("Failed to update kcminputrc cursor theme: %v", err)
		return
	}
	log.Printf("Set kcminputrc cursor theme to %s", cursorTheme)
	_ = exec.Command("qdbus", "org.kde.KWin", "/KWin", "reconfigureAll").Run()
}

func isNotFound(err error) bool {
	var execErr *exec.Error
	return errors.As(err, &execErr)
}

// writeKDEColorscheme mirrors KDESystemAdapter._write_kde_colorscheme:
// best-effort, failures are logged and swallowed.
func (KDEAdapter) writeKDEColorscheme(mode string, palette theme.Palette) {
	defer func() {
		if r := recover(); r != nil {
			log.Printf("Failed to write KDE colorscheme: %v", r)
		}
	}()

	tokens := theme.PaletteToTokens(palette, mode)
	accentTokens := theme.PaletteToAccentTokens(palette, mode)

	home, err := os.UserHomeDir()
	if err != nil {
		log.Printf("Failed to write KDE colorscheme: %v", err)
		return
	}
	schemeDir := filepath.Join(home, ".local", "share", "color-schemes")
	if err := os.MkdirAll(schemeDir, 0o755); err != nil {
		log.Printf("Failed to write KDE colorscheme: %v", err)
		return
	}
	schemePath := filepath.Join(schemeDir, kdeColorschemeName+".colors")
	content := buildKDEColorscheme(tokens, accentTokens)
	if err := os.WriteFile(schemePath, []byte(content), 0o644); err != nil {
		log.Printf("Failed to write KDE colorscheme: %v", err)
		return
	}
	log.Printf("Wrote KDE colorscheme: %s", schemePath)
}

func rgbTriplet(hexColor string) string {
	r, g, b := theme.HexToRGB(hexColor)
	return fmt.Sprintf("%d,%d,%d", r, g, b)
}

func colorGroup(bgNormal, bgAlt, fgNormal, fgInactive, active, link, negative, neutral, positive, visited, deco string) string {
	return fmt.Sprintf(
		"BackgroundAlternate=%s\nBackgroundNormal=%s\nDecorationFocus=%s\nDecorationHover=%s\nForegroundActive=%s\nForegroundInactive=%s\nForegroundLink=%s\nForegroundNegative=%s\nForegroundNeutral=%s\nForegroundNormal=%s\nForegroundPositive=%s\nForegroundVisited=%s\n",
		rgbTriplet(bgAlt), rgbTriplet(bgNormal), rgbTriplet(deco), rgbTriplet(deco),
		rgbTriplet(active), rgbTriplet(fgInactive), rgbTriplet(link), rgbTriplet(negative),
		rgbTriplet(neutral), rgbTriplet(fgNormal), rgbTriplet(positive), rgbTriplet(visited),
	)
}

func buildKDEColorscheme(tokens, accentTokens map[string]string) string {
	bg := tokens["bg"]
	fg := tokens["fg"]
	muted := tokens["muted"]
	primary := tokens["primary"]
	success := tokens["success"]
	warning := tokens["warning"]
	errorColor := tokens["error"]
	info := tokens["info"]
	surface1 := tokens["surface_1"]
	surface2 := tokens["surface_2"]
	accent := accentTokens["accent_primary"]
	accentSelection := accentTokens["accent_selection"]

	windowGroup := colorGroup(surface1, surface2, fg, muted, accent, info, errorColor, warning, success, primary, accent)
	buttonGroup := colorGroup(surface1, surface2, fg, muted, accent, info, errorColor, warning, success, primary, accent)
	viewGroup := colorGroup(bg, surface1, fg, muted, accent, info, errorColor, warning, success, primary, accent)
	selectionGroup := colorGroup(accent, accentSelection, bg, muted, accent, info, errorColor, warning, success, primary, accent)
	tooltipGroup := colorGroup(surface1, surface2, fg, muted, accent, info, errorColor, warning, success, primary, accent)
	headerGroup := colorGroup(surface2, surface1, fg, muted, accent, info, errorColor, warning, success, primary, accent)

	lines := []string{
		"[ColorEffects:Disabled]",
		"Color=56,56,56",
		"ColorAmount=0",
		"ColorEffect=0",
		"ContrastAmount=0.65",
		"ContrastEffect=1",
		"IntensityAmount=0.1",
		"IntensityEffect=2",
		"",
		"[ColorEffects:Inactive]",
		"ChangeSelectionColor=true",
		fmt.Sprintf("Color=%s", rgbTriplet(muted)),
		"ColorAmount=0.025",
		"ColorEffect=2",
		"ContrastAmount=0.1",
		"ContrastEffect=2",
		"Enable=false",
		"IntensityAmount=0",
		"IntensityEffect=0",
		"",
		"[Colors:Button]",
		buttonGroup,
		"[Colors:Complementary]",
		viewGroup,
		"[Colors:Header]",
		headerGroup,
		"[Colors:Selection]",
		selectionGroup,
		"[Colors:Tooltip]",
		tooltipGroup,
		"[Colors:View]",
		viewGroup,
		"[Colors:Window]",
		windowGroup,
		"[General]",
		fmt.Sprintf("ColorScheme=%s", kdeColorschemeName),
		"Name=Daybreak Theme",
		"shadeSortColumn=true",
		"",
		"[KDE]",
		"contrast=4",
		"",
		"[WM]",
		fmt.Sprintf("activeBackground=%s", rgbTriplet(surface1)),
		fmt.Sprintf("activeForeground=%s", rgbTriplet(fg)),
		fmt.Sprintf("inactiveBackground=%s", rgbTriplet(bg)),
		fmt.Sprintf("inactiveForeground=%s", rgbTriplet(muted)),
		"",
	}
	return strings.Join(lines, "\n")
}
