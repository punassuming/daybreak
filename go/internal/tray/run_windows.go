//go:build windows

package tray

import (
	"log"
	"os"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"

	"daybreak/internal/orchestrator"
)

// --- Win32 struct layouts, mirroring the ctypes Structures in windows_tray.py ---

type wndClassW struct {
	style      uint32
	wndProc    uintptr
	clsExtra   int32
	wndExtra   int32
	instance   windows.Handle
	icon       windows.Handle
	cursor     windows.Handle
	background windows.Handle
	menuName   *uint16
	className  *uint16
}

type pointT struct {
	x, y int32
}

type msgT struct {
	hwnd    windows.HWND
	message uint32
	wParam  uintptr
	lParam  uintptr
	time    uint32
	pt      pointT
}

type notifyIconDataW struct {
	cbSize            uint32
	hWnd              windows.HWND
	uID               uint32
	uFlags            uint32
	uCallbackMessage  uint32
	hIcon             windows.Handle
	szTip             [128]uint16
	dwState           uint32
	dwStateMask       uint32
	szInfo            [256]uint16
	uTimeoutOrVersion uint32
	szInfoTitle       [64]uint16
	dwInfoFlags       uint32
	guidItem          [16]byte
	hBalloonIcon      windows.Handle
}

type bitmapV5Header struct {
	size          uint32
	width         int32
	height        int32
	planes        uint16
	bitCount      uint16
	compression   uint32
	sizeImage     uint32
	xPelsPerMeter int32
	yPelsPerMeter int32
	clrUsed       uint32
	clrImportant  uint32
	redMask       uint32
	greenMask     uint32
	blueMask      uint32
	alphaMask     uint32
	csType        uint32
	endpoints     [36]byte
	gammaRed      uint32
	gammaGreen    uint32
	gammaBlue     uint32
	intent        uint32
	profileData   uint32
	profileSize   uint32
	reserved      uint32
}

type iconInfo struct {
	fIcon    int32
	xHotspot uint32
	yHotspot uint32
	hbmMask  windows.Handle
	hbmColor windows.Handle
}

const (
	wmDestroy       = 0x0002
	wmContextMenu   = 0x007B
	wmRButtonDown   = 0x0204
	wmRButtonUp     = 0x0205
	wmLButtonUp     = 0x0202
	wmLButtonDblClk = 0x0203
	wmNull          = 0x0000
	wsOverlapped    = 0x00000000
	cwUseDefault    = 0x80000000

	nimAdd        = 0x00000000
	nimModify     = 0x00000001
	nimDelete     = 0x00000002
	nimSetVersion = 0x00000004

	nifMessage = 0x00000001
	nifIcon    = 0x00000002
	nifTip     = 0x00000004

	notifyIconVersion4 = 4

	mfString    = 0x00000000
	mfGrayed    = 0x00000001
	mfDisabled  = 0x00000002
	mfSeparator = 0x00000800
	mfChecked   = 0x00000008

	tpmRightButton = 0x0002
	tpmNoNotify    = 0x0080
	tpmReturnCmd   = 0x0100

	biBitfields  = 3
	dibRgbColors = 0

	ninSelect    = 0x0400
	ninKeySelect = 0x0401

	idiApplication = 32512
	idcArrow       = 32512
)

var (
	user32   = windows.NewLazySystemDLL("user32.dll")
	shell32  = windows.NewLazySystemDLL("shell32.dll")
	gdi32    = windows.NewLazySystemDLL("gdi32.dll")
	kernel32 = windows.NewLazySystemDLL("kernel32.dll")

	procSetProcessDPIAware  = user32.NewProc("SetProcessDPIAware")
	procRegisterClassW      = user32.NewProc("RegisterClassW")
	procCreateWindowExW     = user32.NewProc("CreateWindowExW")
	procDefWindowProcW      = user32.NewProc("DefWindowProcW")
	procDestroyWindow       = user32.NewProc("DestroyWindow")
	procLoadIconW           = user32.NewProc("LoadIconW")
	procLoadCursorW         = user32.NewProc("LoadCursorW")
	procCreatePopupMenu     = user32.NewProc("CreatePopupMenu")
	procDestroyMenu         = user32.NewProc("DestroyMenu")
	procAppendMenuW         = user32.NewProc("AppendMenuW")
	procGetCursorPos        = user32.NewProc("GetCursorPos")
	procSetForegroundWindow = user32.NewProc("SetForegroundWindow")
	procTrackPopupMenu      = user32.NewProc("TrackPopupMenu")
	procPostMessageW        = user32.NewProc("PostMessageW")
	procGetMessageW         = user32.NewProc("GetMessageW")
	procTranslateMessage    = user32.NewProc("TranslateMessage")
	procDispatchMessageW    = user32.NewProc("DispatchMessageW")
	procPostQuitMessage     = user32.NewProc("PostQuitMessage")
	procCreateIconIndirect  = user32.NewProc("CreateIconIndirect")
	procDestroyIcon         = user32.NewProc("DestroyIcon")

	procShellNotifyIconW = shell32.NewProc("Shell_NotifyIconW")

	procCreateDIBSection = gdi32.NewProc("CreateDIBSection")
	procCreateBitmap     = gdi32.NewProc("CreateBitmap")
	procDeleteObject     = gdi32.NewProc("DeleteObject")

	procGetModuleHandleW = kernel32.NewProc("GetModuleHandleW")
	procCreateActCtxW    = kernel32.NewProc("CreateActCtxW")
	procActivateActCtx   = kernel32.NewProc("ActivateActCtx")
)

type actCtxW struct {
	cbSize                 uint32
	dwFlags                uint32
	lpSource               *uint16
	wProcessorArchitecture uint16
	wLangId                uint16
	lpAssemblyDirectory    *uint16
	lpResourceName         *uint16
	lpApplicationName      *uint16
	hModule                windows.Handle
}

// activateVisualStyles mirrors windows_tray._activate_visual_styles: loads
// a tiny inline manifest requesting comctl32 v6 so menus/controls get
// modern (and dark-mode-capable) visual styles.
func activateVisualStyles() {
	defer func() { recover() }()

	manifest := `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>` +
		`<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">` +
		`<dependency><dependentAssembly>` +
		`<assemblyIdentity type="win32" name="Microsoft.Windows.Common-Controls"` +
		` version="6.0.0.0" processorArchitecture="*"` +
		` publicKeyToken="6595b64144ccf1df" language="*"/>` +
		`</dependentAssembly></dependency>` +
		`</assembly>`

	f, err := os.CreateTemp("", "daybreak-*.manifest")
	if err != nil {
		return
	}
	path := f.Name()
	_, _ = f.WriteString(manifest)
	f.Close()
	defer os.Remove(path)

	pathPtr, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return
	}

	act := actCtxW{
		lpSource: pathPtr,
	}
	act.cbSize = uint32(unsafe.Sizeof(act))

	h, _, _ := procCreateActCtxW.Call(uintptr(unsafe.Pointer(&act)))
	if h == 0 || h == ^uintptr(0) {
		return
	}
	var cookie uintptr
	procActivateActCtx.Call(h, uintptr(unsafe.Pointer(&cookie)))
}

// setupDarkMode mirrors windows_tray._setup_dark_mode: undocumented
// uxtheme ordinals that let the tray's popup menu render in dark mode on
// Windows 10 1903+.
func setupDarkMode(hwnd windows.HWND) {
	defer func() { recover() }()

	uxtheme, err := windows.LoadLibrary("uxtheme.dll")
	if err != nil {
		return
	}
	defer windows.FreeLibrary(uxtheme)

	getProcAddress := kernel32.NewProc("GetProcAddress")

	callOrdinal := func(ordinal uintptr, args ...uintptr) {
		addr, _, _ := getProcAddress.Call(uintptr(uxtheme), ordinal)
		if addr == 0 {
			return
		}
		switch len(args) {
		case 0:
			syscallCall(addr)
		case 1:
			syscallCall(addr, args[0])
		case 2:
			syscallCall(addr, args[0], args[1])
		}
	}

	// Ordinal 135: SetPreferredAppMode(1 = AllowDark)
	callOrdinal(135, 1)
	// Ordinal 133: AllowDarkModeForWindow(hwnd, true)
	if hwnd != 0 {
		callOrdinal(133, uintptr(hwnd), 1)
	}
	// Ordinal 136: FlushMenuThemes()
	callOrdinal(136)
}

func syscallCall(addr uintptr, args ...uintptr) {
	var a0, a1, a2 uintptr
	if len(args) > 0 {
		a0 = args[0]
	}
	if len(args) > 1 {
		a1 = args[1]
	}
	if len(args) > 2 {
		a2 = args[2]
	}
	syscall.Syscall(addr, uintptr(len(args)), a0, a1, a2)
}

func signedWord(value uintptr) int {
	word := int32(uint16(value))
	if word&0x8000 != 0 {
		return int(word) - 0x10000
	}
	return int(word)
}

func menuPositionFromWParam(wParam uintptr) (x, y int, ok bool) {
	if wParam == 0 {
		return 0, 0, false
	}
	xPos := signedWord(wParam)
	yPos := signedWord(wParam >> 16)
	if xPos == -1 && yPos == -1 {
		return 0, 0, false
	}
	return xPos, yPos, true
}

func makeIntResource(id uint16) *uint16 {
	return (*uint16)(unsafe.Pointer(uintptr(id)))
}

// Run mirrors windows_tray.run_windows_tray.
func Run(orch *orchestrator.Orchestrator) error {
	procSetProcessDPIAware.Call()
	activateVisualStyles()

	controller := NewController(orch)
	className, _ := windows.UTF16PtrFromString("DaybreakTrayWindow")
	windowTitle, _ := windows.UTF16PtrFromString("Daybreak")

	hInstance, _, _ := procGetModuleHandleW.Call(0)

	createTrayIcon := func(mode string) windows.Handle {
		pixels := renderModeIconPixels(mode, 32)

		header := bitmapV5Header{
			width:       32,
			height:      -32,
			planes:      1,
			bitCount:    32,
			compression: biBitfields,
			sizeImage:   uint32(len(pixels)),
			redMask:     0x00FF0000,
			greenMask:   0x0000FF00,
			blueMask:    0x000000FF,
			alphaMask:   0xFF000000,
		}
		header.size = uint32(unsafe.Sizeof(header))

		var bits uintptr
		colorBitmap, _, _ := procCreateDIBSection.Call(0, uintptr(unsafe.Pointer(&header)), dibRgbColors, uintptr(unsafe.Pointer(&bits)), 0, 0)
		if colorBitmap == 0 || bits == 0 {
			return 0
		}

		maskBitmap, _, _ := procCreateBitmap.Call(32, 32, 1, 1, 0)
		if maskBitmap == 0 {
			procDeleteObject.Call(colorBitmap)
			return 0
		}

		dst := unsafe.Slice((*byte)(unsafe.Pointer(bits)), len(pixels))
		copy(dst, pixels)

		info := iconInfo{
			fIcon:    1,
			hbmMask:  windows.Handle(maskBitmap),
			hbmColor: windows.Handle(colorBitmap),
		}
		icon, _, _ := procCreateIconIndirect.Call(uintptr(unsafe.Pointer(&info)))

		procDeleteObject.Call(maskBitmap)
		procDeleteObject.Call(colorBitmap)

		return windows.Handle(icon)
	}

	iconHandles := map[string]windows.Handle{
		"light": createTrayIcon("light"),
		"dark":  createTrayIcon("dark"),
	}
	if iconHandles["light"] == 0 || iconHandles["dark"] == 0 {
		fallback, _, _ := procLoadIconW.Call(0, uintptr(unsafe.Pointer(makeIntResource(idiApplication))))
		if iconHandles["light"] == 0 {
			iconHandles["light"] = windows.Handle(fallback)
		}
		if iconHandles["dark"] == 0 {
			iconHandles["dark"] = windows.Handle(fallback)
		}
	}

	cursorHandle, _, _ := procLoadCursorW.Call(0, uintptr(unsafe.Pointer(makeIntResource(idcArrow))))

	var hwnd windows.HWND

	currentIconHandle := func() windows.Handle {
		if h, ok := iconHandles[controller.CurrentMode]; ok {
			return h
		}
		return iconHandles["light"]
	}

	updateTrayIcon := func() {
		if hwnd == 0 {
			return
		}
		var data notifyIconDataW
		data.cbSize = uint32(unsafe.Sizeof(data))
		data.hWnd = hwnd
		data.uID = 1
		data.uFlags = nifTip | nifIcon
		data.hIcon = currentIconHandle()
		copyToUTF16Array(data.szTip[:], controller.TooltipText())
		procShellNotifyIconW.Call(nimModify, uintptr(unsafe.Pointer(&data)))
	}

	buildMenu := func() uintptr {
		menuHandle, _, _ := procCreatePopupMenu.Call()
		if menuHandle == 0 {
			return 0
		}

		currentFlags := uintptr(mfString | mfDisabled | mfGrayed)
		lightFlags := uintptr(mfString)
		if controller.CurrentMode == "light" {
			lightFlags |= mfChecked
		}
		darkFlags := uintptr(mfString)
		if controller.CurrentMode == "dark" {
			darkFlags |= mfChecked
		}

		appendMenu := func(flags uintptr, id uintptr, text string) {
			t, _ := windows.UTF16PtrFromString(text)
			procAppendMenuW.Call(menuHandle, flags, id, uintptr(unsafe.Pointer(t)))
		}
		appendSeparator := func() {
			procAppendMenuW.Call(menuHandle, mfSeparator, 0, 0)
		}

		appendMenu(currentFlags, 0, controller.StatusText())
		appendSeparator()
		appendMenu(mfString, idToggle, "Toggle")
		appendMenu(lightFlags, idLight, "Switch to Light")
		appendMenu(darkFlags, idDark, "Switch to Dark")
		appendSeparator()
		appendMenu(mfString, idOpenConfig, "Open Config")
		appendMenu(mfString, idRunSetup, "Run Setup")
		appendSeparator()
		appendMenu(mfString, idExit, "Exit")

		return menuHandle
	}

	showMenu := func(anchor *[2]int) {
		var pt pointT
		if anchor == nil {
			procGetCursorPos.Call(uintptr(unsafe.Pointer(&pt)))
		} else {
			pt.x, pt.y = int32(anchor[0]), int32(anchor[1])
		}
		procSetForegroundWindow.Call(uintptr(hwnd))
		menuHandle := buildMenu()
		commandID, _, _ := procTrackPopupMenu.Call(
			menuHandle,
			tpmRightButton|tpmNoNotify|tpmReturnCmd,
			uintptr(pt.x),
			uintptr(pt.y),
			0,
			uintptr(hwnd),
			0,
		)
		procPostMessageW.Call(uintptr(hwnd), wmNull, 0, 0)
		procDestroyMenu.Call(menuHandle)
		if commandID != 0 {
			if !controller.HandleCommand(int(commandID)) {
				procDestroyWindow.Call(uintptr(hwnd))
				return
			}
			updateTrayIcon()
		}
	}

	windowProc := windows.NewCallback(func(windowHandle windows.HWND, message uint32, wParam, lParam uintptr) uintptr {
		if message == trayCallbackMessage {
			notificationCode := uint32(lParam) & 0xFFFF
			x, y, hasAnchor := menuPositionFromWParam(wParam)
			var anchor *[2]int
			if hasAnchor {
				anchor = &[2]int{x, y}
			}

			switch notificationCode {
			case wmContextMenu, wmRButtonDown, wmRButtonUp, wmLButtonUp, ninSelect, ninKeySelect:
				showMenu(anchor)
				return 0
			case wmLButtonDblClk:
				controller.ToggleMode()
				updateTrayIcon()
				return 0
			}
			return 0
		}

		if message == wmDestroy {
			var data notifyIconDataW
			data.cbSize = uint32(unsafe.Sizeof(data))
			data.hWnd = windowHandle
			data.uID = 1
			procShellNotifyIconW.Call(nimDelete, uintptr(unsafe.Pointer(&data)))
			procPostQuitMessage.Call(0)
			return 0
		}

		ret, _, _ := procDefWindowProcW.Call(uintptr(windowHandle), uintptr(message), wParam, lParam)
		return ret
	})

	windowClass := wndClassW{
		wndProc:   windowProc,
		instance:  windows.Handle(hInstance),
		className: className,
		icon:      currentIconHandle(),
		cursor:    windows.Handle(cursorHandle),
	}

	if ok, _, _ := procRegisterClassW.Call(uintptr(unsafe.Pointer(&windowClass))); ok == 0 {
		return errString("failed to register Daybreak tray window class")
	}

	hwndRaw, _, _ := procCreateWindowExW.Call(
		0,
		uintptr(unsafe.Pointer(className)),
		uintptr(unsafe.Pointer(windowTitle)),
		wsOverlapped,
		cwUseDefault, cwUseDefault, cwUseDefault, cwUseDefault,
		0, 0,
		hInstance,
		0,
	)
	if hwndRaw == 0 {
		return errString("failed to create Daybreak tray window")
	}
	hwnd = windows.HWND(hwndRaw)

	setupDarkMode(hwnd)

	var data notifyIconDataW
	data.cbSize = uint32(unsafe.Sizeof(data))
	data.hWnd = hwnd
	data.uID = 1
	data.uFlags = nifMessage | nifIcon | nifTip
	data.uCallbackMessage = trayCallbackMessage
	data.hIcon = currentIconHandle()
	copyToUTF16Array(data.szTip[:], controller.TooltipText())

	if ok, _, _ := procShellNotifyIconW.Call(nimAdd, uintptr(unsafe.Pointer(&data))); ok == 0 {
		procDestroyWindow.Call(uintptr(hwnd))
		return errString("failed to add Daybreak tray icon")
	}

	data.uTimeoutOrVersion = notifyIconVersion4
	procShellNotifyIconW.Call(nimSetVersion, uintptr(unsafe.Pointer(&data)))

	log.Printf("Daybreak tray is running.")

	var message msgT
	for {
		result, _, _ := procGetMessageW.Call(uintptr(unsafe.Pointer(&message)), 0, 0, 0)
		if int32(result) == -1 {
			procDestroyWindow.Call(uintptr(hwnd))
			return errString("Daybreak tray message loop failed")
		}
		if result == 0 {
			break
		}
		procTranslateMessage.Call(uintptr(unsafe.Pointer(&message)))
		procDispatchMessageW.Call(uintptr(unsafe.Pointer(&message)))
	}

	seen := map[windows.Handle]bool{}
	for _, icon := range iconHandles {
		if icon != 0 && !seen[icon] {
			seen[icon] = true
			procDestroyIcon.Call(uintptr(icon))
		}
	}

	return nil
}

func copyToUTF16Array(dst []uint16, s string) {
	encoded, err := windows.UTF16FromString(s)
	if err != nil {
		return
	}
	n := len(encoded)
	if n > len(dst) {
		n = len(dst)
	}
	copy(dst, encoded[:n])
	if n > 0 && n == len(dst) {
		dst[len(dst)-1] = 0
	}
}

type errString string

func (e errString) Error() string { return string(e) }
