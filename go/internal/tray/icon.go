// Package tray: shared icon-pixel rendering, used by both the Windows
// (windows.go) and Linux (linux.go) tray backends — the math has no OS
// dependency, so unlike the rest of this package it carries no build tag.
package tray

import "math"

// Menu command ids, shared by the Windows and Linux tray backends.
const (
	idToggle     = 1001
	idLight      = 1002
	idDark       = 1003
	idExit       = 1004
	idOpenConfig = 1005
	idRunSetup   = 1006
)

// RenderModeIconPixels mirrors windows_tray._render_mode_icon_pixels: a
// hand-drawn 32x32 BGRA sun (light) or crescent moon + stars (dark) icon.
func RenderModeIconPixels(mode string, size int) []byte {
	pixels := make([]byte, size*size*4)
	center := float64(size-1) / 2.0
	sunRadius := float64(size) * 0.22
	rayInner := float64(size) * 0.29
	rayOuter := float64(size) * 0.44
	moonRadius := float64(size) * 0.28
	moonCutout := float64(size) * 0.24

	setPixel := func(x, y int, red, green, blue, alpha byte) {
		if x < 0 || x >= size || y < 0 || y >= size {
			return
		}
		offset := (y*size + x) * 4
		pixels[offset] = blue
		pixels[offset+1] = green
		pixels[offset+2] = red
		pixels[offset+3] = alpha
	}

	distance := func(x, y, cx, cy float64) float64 {
		return math.Hypot(x-cx, y-cy)
	}

	if mode == "light" {
		for y := 0; y < size; y++ {
			for x := 0; x < size; x++ {
				px := float64(x) + 0.5
				py := float64(y) + 0.5
				d := distance(px, py, center, center)
				if d <= sunRadius {
					setPixel(x, y, 255, 198, 72, 255)
					continue
				}

				dx := math.Abs(px - center)
				dy := math.Abs(py - center)
				onVertical := dx <= float64(size)*0.06 && d >= rayInner && d <= rayOuter
				onHorizontal := dy <= float64(size)*0.06 && d >= rayInner && d <= rayOuter
				onDiagA := math.Abs((px-center)-(py-center)) <= float64(size)*0.08 && d >= rayInner && d <= rayOuter
				onDiagB := math.Abs((px-center)+(py-center)) <= float64(size)*0.08 && d >= rayInner && d <= rayOuter

				if onVertical || onHorizontal || onDiagA || onDiagB {
					setPixel(x, y, 255, 224, 128, 235)
				}
			}
		}
	} else {
		moonCenterX := center + float64(size)*0.02
		moonCenterY := center - float64(size)*0.02
		cutoutCenterX := center + float64(size)*0.16
		cutoutCenterY := center - float64(size)*0.08

		for y := 0; y < size; y++ {
			for x := 0; x < size; x++ {
				px := float64(x) + 0.5
				py := float64(y) + 0.5
				outer := distance(px, py, moonCenterX, moonCenterY) <= moonRadius
				inner := distance(px, py, cutoutCenterX, cutoutCenterY) <= moonCutout
				if outer && !inner {
					setPixel(x, y, 192, 222, 255, 255)
				}
			}
		}

		for _, star := range [][2]int{{9, 9}, {22, 8}, {24, 21}} {
			for _, d := range [][2]int{{0, 0}, {-1, 0}, {1, 0}, {0, -1}, {0, 1}} {
				setPixel(star[0]+d[0], star[1]+d[1], 255, 244, 202, 220)
			}
		}
	}

	return pixels
}
