//go:build windows

// Package system ports adapters/system/windows.py and adapters/system/kde.py:
// the OS-level "apply this mode" side effects.
package system

import (
	"fmt"
	"log"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
	"golang.org/x/sys/windows/registry"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

const personalizeKeyPath = `Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`

// WindowsAdapter mirrors adapters/system/windows.py's WindowsSystemAdapter,
// plus optional cursor-scheme switching (not in the Python original).
type WindowsAdapter struct {
	Config *config.Manager
}

func (WindowsAdapter) Name() string { return "windows" }

// GetCurrentMode mirrors WindowsSystemAdapter.get_current_mode.
func (WindowsAdapter) GetCurrentMode() (string, error) {
	key, err := registry.OpenKey(registry.CURRENT_USER, personalizeKeyPath, registry.QUERY_VALUE)
	if err != nil {
		log.Printf("Failed to read Windows registry: %v", err)
		return "light", nil
	}
	defer key.Close()

	value, _, err := key.GetIntegerValue("AppsUseLightTheme")
	if err != nil {
		log.Printf("Failed to read Windows registry: %v", err)
		return "light", nil
	}
	if value == 1 {
		return "light", nil
	}
	return "dark", nil
}

// SetMode mirrors WindowsSystemAdapter.set_mode: writes both theme
// registry keys, then broadcasts WM_SETTINGCHANGE so running apps notice.
// Also applies a configured cursor scheme for the mode, if any (an
// addition beyond the Python original).
func (a WindowsAdapter) SetMode(mode string, _ theme.Palette) {
	value := uint32(1)
	if mode != "light" {
		value = 0
	}

	key, err := registry.OpenKey(registry.CURRENT_USER, personalizeKeyPath, registry.SET_VALUE)
	if err != nil {
		log.Printf("Failed to change Windows theme: %v", err)
		return
	}
	defer key.Close()

	if err := key.SetDWordValue("AppsUseLightTheme", value); err != nil {
		log.Printf("Failed to change Windows theme: %v", err)
		return
	}
	if err := key.SetDWordValue("SystemUsesLightTheme", value); err != nil {
		log.Printf("Failed to change Windows theme: %v", err)
		return
	}

	log.Printf("Registry updated for %s mode.", mode)
	broadcastThemeChange()
	log.Printf("Broadcasted WM_SETTINGCHANGE.")

	if a.Config != nil {
		schemeName := a.Config.Data.System.WindowsCursorDark
		if mode == "light" {
			schemeName = a.Config.Data.System.WindowsCursorLight
		}
		if schemeName != "" {
			if err := applyCursorScheme(schemeName); err != nil {
				log.Printf("Failed to apply cursor scheme '%s': %v", schemeName, err)
			} else {
				log.Printf("Applied cursor scheme '%s'.", schemeName)
			}
		}
	}
}

// cursorValueNames is the fixed field order Windows uses inside a cursor
// scheme's comma-separated registry string (confirmed against this
// machine's live HKCU\Control Panel\Cursors values, whose field names
// match this list exactly; e.g. the built-in "Windows Default" scheme is
// literally stored as 14 commas — 15 empty fields in this order).
var cursorValueNames = []string{
	"Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen",
	"No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand",
}

// applyCursorScheme mirrors what Control Panel's Mouse > Pointers tab does
// when you pick a scheme from the dropdown: copy each cursor path out of
// HKCU\Control Panel\Cursors\Schemes\<name> into the individual
// HKCU\Control Panel\Cursors values, then tell Windows to reload cursors
// via SystemParametersInfoW(SPI_SETCURSORS).
//
// This only works for scheme names already registered under
// HKCU\Control Panel\Cursors\Schemes — which happens the first time a
// scheme is selected (or explicitly saved) via Settings/Control Panel.
// Windows' built-in scheme catalog (Windows Black, Windows Aero, etc.) is
// otherwise embedded as shell32.dll string resources, not plain registry
// values, so this can't apply a built-in scheme the user has never
// selected at least once.
func applyCursorScheme(schemeName string) error {
	schemesKey, err := registry.OpenKey(registry.CURRENT_USER, `Control Panel\Cursors\Schemes`, registry.QUERY_VALUE)
	if err != nil {
		return fmt.Errorf("no saved cursor schemes found (select '%s' at least once via Settings > Mouse first): %w", schemeName, err)
	}
	defer schemesKey.Close()

	schemeValue, _, err := schemesKey.GetStringValue(schemeName)
	if err != nil {
		return fmt.Errorf("cursor scheme '%s' not found under HKCU\\Control Panel\\Cursors\\Schemes: %w", schemeName, err)
	}

	paths := strings.Split(schemeValue, ",")

	cursorsKey, err := registry.OpenKey(registry.CURRENT_USER, `Control Panel\Cursors`, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer cursorsKey.Close()

	for i, valueName := range cursorValueNames {
		if i >= len(paths) {
			break
		}
		path := strings.TrimSpace(paths[i])
		if path == "" {
			continue
		}
		if err := cursorsKey.SetStringValue(valueName, path); err != nil {
			return fmt.Errorf("failed to set cursor value %s: %w", valueName, err)
		}
	}
	if err := cursorsKey.SetStringValue("", schemeName); err != nil {
		return err
	}

	const (
		spiSetCursors     = 0x0057
		spifUpdateINIFile = 0x0001
		spifSendChange    = 0x0002
	)
	user32 := windows.NewLazySystemDLL("user32.dll")
	systemParametersInfoW := user32.NewProc("SystemParametersInfoW")
	systemParametersInfoW.Call(spiSetCursors, 0, 0, spifUpdateINIFile|spifSendChange)

	return nil
}

const (
	hwndBroadcast   = 0xFFFF
	wmSettingChange = 0x001A
	smtoAbortIfHung = 0x0002
)

// broadcastThemeChange mirrors WindowsSystemAdapter._broadcast_theme_change:
// prefer the async SendNotifyMessage, fall back to a timed SendMessage.
func broadcastThemeChange() {
	user32 := windows.NewLazySystemDLL("user32.dll")
	sendNotifyMessageW := user32.NewProc("SendNotifyMessageW")
	sendMessageTimeoutW := user32.NewProc("SendMessageTimeoutW")

	paramPtr, err := windows.UTF16PtrFromString("ImmersiveColorSet")
	if err != nil {
		return
	}

	ret, _, _ := sendNotifyMessageW.Call(
		uintptr(hwndBroadcast),
		uintptr(wmSettingChange),
		0,
		uintptr(unsafe.Pointer(paramPtr)),
	)
	if ret != 0 {
		return
	}

	var result uintptr
	sendMessageTimeoutW.Call(
		uintptr(hwndBroadcast),
		uintptr(wmSettingChange),
		0,
		uintptr(unsafe.Pointer(paramPtr)),
		uintptr(smtoAbortIfHung),
		5000,
		uintptr(unsafe.Pointer(&result)),
	)
}
