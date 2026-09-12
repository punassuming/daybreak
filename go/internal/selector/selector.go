// Package selector ports interactive.py's curses-based theme picker to a
// cross-platform tcell TUI.
//
// interactive.py hard-imports stdlib `curses`, which Windows Python doesn't
// ship (no `_curses` module without the third-party windows-curses
// package) — so `daybreak select` is simply broken on Windows today. tcell
// works on both Windows consoles and POSIX terminals with no extra system
// dependency, which is the whole point of this port.
//
// One deliberate behavior change: the Python picker recolors the *entire*
// enclosing terminal live while browsing (it broadcasts real OSC 4/10/11/12
// sequences to /dev/pts via UniversalPty, POSIX-only) in addition to
// drawing its own in-app preview mockup (16-color blocks, a fake code
// snippet, a diff view, a status bar) using curses's 16-slot color-pair
// palette. This port keeps the in-app preview — rendered in true 24-bit
// color instead of 16 remapped ANSI slots, so it's actually more accurate —
// but drops the real-terminal OSC broadcast: injecting raw escape codes
// into a live tcell session risks corrupting tcell's own render state, and
// the broadcast never worked on Windows anyway (no /dev/pts). Saving still
// only persists config (config.SetModeThemes), exactly like the Python
// original; it does not apply the theme system-wide.
package selector

import (
	"fmt"
	"sort"

	"github.com/gdamore/tcell/v2"

	"daybreak/internal/config"
	"daybreak/internal/theme"
)

// Run mirrors interactive.run_interactive_selector.
func Run(cfg *config.Manager) error {
	screen, err := tcell.NewScreen()
	if err != nil {
		return err
	}
	if err := screen.Init(); err != nil {
		return err
	}
	defer screen.Fini()

	savedLight, savedDark, err := loop(screen, cfg)
	if err != nil {
		return err
	}
	if savedLight != "" || savedDark != "" {
		cfg.SetModeThemes(savedLight, savedDark)
		fmt.Printf("Saved: Light='%s', Dark='%s'\n", savedLight, savedDark)
	}
	return nil
}

func loop(screen tcell.Screen, cfg *config.Manager) (savedLight, savedDark string, err error) {
	themes := theme.ListThemeNames()
	sort.Strings(themes)

	savedLight = cfg.GetModeThemeName("light")
	savedDark = cfg.GetModeThemeName("dark")

	previewMode := "dark"
	currentIdx := 0
	startTheme := savedLight
	if previewMode == "dark" {
		startTheme = savedDark
	}
	for i, t := range themes {
		if t == startTheme {
			currentIdx = i
			break
		}
	}

	selectedStyle := tcell.StyleDefault.Foreground(tcell.ColorBlack).Background(tcell.ColorWhite)

	for {
		screen.Clear()
		width, height := screen.Size()

		title := " Daybreak Theme Selector "
		modeIndicator := fmt.Sprintf(" PREVIEW: %s ", upper(previewMode))
		instructions := fmt.Sprintf(" UP/DOWN: Nav | TAB: Toggle Mode | SPACE: Set %s Default | ENTER: Save & Exit | q: Quit ", upper(previewMode))

		drawText(screen, 0, 0, title, tcell.StyleDefault.Reverse(true).Bold(true))
		drawText(screen, width-len(modeIndicator)-1, 0, modeIndicator, tcell.StyleDefault.Reverse(true))
		drawText(screen, 0, 1, instructions, tcell.StyleDefault)
		drawHLine(screen, 0, 2, width)

		const sidebarWidth = 30
		drawVLine(screen, sidebarWidth, 3, height-3)

		maxItems := height - 4
		if maxItems < 1 {
			maxItems = 1
		}
		startIdx := currentIdx - maxItems/2
		if startIdx < 0 {
			startIdx = 0
		}
		endIdx := startIdx + maxItems
		if endIdx > len(themes) {
			endIdx = len(themes)
		}

		for i := startIdx; i < endIdx; i++ {
			t := themes[i]
			y := 3 + (i - startIdx)

			marker := ""
			if t == savedLight {
				marker += "L"
			}
			if t == savedDark {
				marker += "D"
			}

			style := tcell.StyleDefault
			if i == currentIdx {
				style = selectedStyle
			}
			drawText(screen, 1, y, fmt.Sprintf(" %s %-20s ", center3(marker), t), style)
		}

		set := theme.GetThemePalette(themes[currentIdx])
		palette := set.Dark
		if previewMode == "light" {
			palette = set.Light
		}

		if width > sidebarWidth+20 {
			drawColorBlocks(screen, 4, sidebarWidth+4, palette)
			if height > 20 {
				drawCodeMock(screen, 14, sidebarWidth+4, palette)
			}
			if height > 30 {
				drawExtraMocks(screen, 22, sidebarWidth+4, palette)
			}
		}

		screen.Show()

		ev := screen.PollEvent()
		switch e := ev.(type) {
		case *tcell.EventResize:
			screen.Sync()
		case *tcell.EventKey:
			switch {
			case e.Rune() == 'q':
				return "", "", nil
			case e.Key() == tcell.KeyUp:
				if currentIdx > 0 {
					currentIdx--
				}
			case e.Key() == tcell.KeyDown:
				if currentIdx < len(themes)-1 {
					currentIdx++
				}
			case e.Key() == tcell.KeyTab:
				if previewMode == "dark" {
					previewMode = "light"
				} else {
					previewMode = "dark"
				}
			case e.Rune() == ' ':
				if previewMode == "dark" {
					savedDark = themes[currentIdx]
				} else {
					savedLight = themes[currentIdx]
				}
			case e.Key() == tcell.KeyEnter:
				return savedLight, savedDark, nil
			case e.Key() == tcell.KeyCtrlC:
				return "", "", nil
			}
		}
	}
}

func upper(s string) string {
	out := []rune(s)
	for i, r := range out {
		if r >= 'a' && r <= 'z' {
			out[i] = r - ('a' - 'A')
		}
	}
	return string(out)
}

func center3(s string) string {
	switch len(s) {
	case 0:
		return "   "
	case 1:
		return " " + s + " "
	case 2:
		return s + " "
	default:
		return s[:3]
	}
}

func drawText(screen tcell.Screen, x, y int, text string, style tcell.Style) {
	for i, r := range text {
		screen.SetContent(x+i, y, r, nil, style)
	}
}

func drawHLine(screen tcell.Screen, x, y, width int) {
	for i := 0; i < width; i++ {
		screen.SetContent(x+i, y, tcell.RuneHLine, nil, tcell.StyleDefault)
	}
}

func drawVLine(screen tcell.Screen, x, y, height int) {
	for i := 0; i < height; i++ {
		screen.SetContent(x, y+i, tcell.RuneVLine, nil, tcell.StyleDefault)
	}
}

func hexColor(hex string) tcell.Color {
	if !theme.IsHexColor(hex) {
		return tcell.ColorDefault
	}
	r, g, b := theme.HexToRGB(hex)
	return tcell.NewRGBColor(int32(r), int32(g), int32(b))
}

// drawColorBlocks mirrors interactive._draw_color_blocks, using the
// palette's real truecolor values instead of remapped 16-slot ANSI pairs.
func drawColorBlocks(screen tcell.Screen, y, x int, palette theme.Palette) {
	drawText(screen, x, y, "Palette Preview:", tcell.StyleDefault.Bold(true))

	for i := 0; i < 16; i++ {
		row := 0
		col := i
		if i >= 8 {
			row = 1
			col = i - 8
		}
		hex, ok := palette.Colors[itoa(i)]
		if !ok {
			continue
		}
		bg := hexColor(hex)
		blockY := y + 2 + row*3
		drawText(screen, x+col*4, blockY, "   ", tcell.StyleDefault.Background(bg))
		drawText(screen, x+col*4, blockY+1, fmt.Sprintf(" %d ", i), tcell.StyleDefault)
	}
}

// drawCodeMock mirrors interactive._draw_code_mock.
func drawCodeMock(screen tcell.Screen, y, x int, palette theme.Palette) {
	drawText(screen, x, y, "Code Syntax Mock:", tcell.StyleDefault.Bold(true))

	blue := tcell.StyleDefault.Foreground(hexColor(palette.Colors["4"]))
	yellow := tcell.StyleDefault.Foreground(hexColor(palette.Colors["3"]))
	green := tcell.StyleDefault.Foreground(hexColor(palette.Colors["2"]))
	gray := tcell.StyleDefault.Foreground(hexColor(palette.Colors["8"]))

	drawText(screen, x, y+2, "def ", yellow)
	drawText(screen, x+4, y+2, "calculate_sum", blue)
	drawText(screen, x+17, y+2, "(data):", tcell.StyleDefault)

	drawText(screen, x+4, y+3, "# This is a comment", gray)

	drawText(screen, x+4, y+4, "if ", yellow)
	drawText(screen, x+7, y+4, "not ", yellow)
	drawText(screen, x+11, y+4, "data: ", tcell.StyleDefault)

	drawText(screen, x+8, y+5, "return ", yellow)
	drawText(screen, x+15, y+5, `"Error"`, green)
}

// drawExtraMocks mirrors interactive._draw_extra_mocks.
func drawExtraMocks(screen tcell.Screen, y, x int, palette theme.Palette) {
	drawText(screen, x, y, "Git Diff Mock:", tcell.StyleDefault.Bold(true))
	green := tcell.StyleDefault.Foreground(hexColor(palette.Colors["2"]))
	red := tcell.StyleDefault.Foreground(hexColor(palette.Colors["1"]))
	drawText(screen, x, y+2, "+ def new_feature():", green)
	drawText(screen, x, y+3, "+     return True", green)
	drawText(screen, x, y+4, "- def old_buggy_code():", red)

	drawText(screen, x+30, y, "Search Highlight:", tcell.StyleDefault.Bold(true))
	searchStyle := tcell.StyleDefault.Foreground(hexColor(palette.Colors["0"])).Background(hexColor(palette.Colors["3"]))
	drawText(screen, x+30, y+2, "grep 'pattern' file.txt", tcell.StyleDefault)
	drawText(screen, x+30, y+3, "Found: ", tcell.StyleDefault)
	drawText(screen, x+37, y+3, "pattern", searchStyle)
	drawText(screen, x+44, y+3, " in line 42", tcell.StyleDefault)

	drawText(screen, x, y+6, "Status Bar:", tcell.StyleDefault.Bold(true))
	statusStyle := tcell.StyleDefault.Foreground(hexColor(palette.Colors["15"])).Background(hexColor(palette.Colors["4"]))
	dimStyle := tcell.StyleDefault.Foreground(hexColor(palette.Colors["15"])).Background(hexColor(palette.Colors["8"]))
	statusText := " NORMAL  master  daybreak/interactive.py "
	drawText(screen, x, y+8, statusText, statusStyle)
	drawText(screen, x+len(statusText), y+8, " 90% ", dimStyle)
}

func itoa(i int) string {
	return fmt.Sprintf("%d", i)
}
