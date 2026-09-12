// Package theme ports daybreak's palette/token engine (colors.py, themes.py,
// theme_model.py, theme_transform.py, theme_registry.py) from Python to Go.
package theme

import (
	"fmt"
	"math"
	"strconv"
	"strings"
)

// HexToRGB parses a "#rrggbb" string into 0-255 component values.
func HexToRGB(hex string) (r, g, b int) {
	hex = strings.TrimPrefix(hex, "#")
	rv, _ := strconv.ParseInt(hex[0:2], 16, 32)
	gv, _ := strconv.ParseInt(hex[2:4], 16, 32)
	bv, _ := strconv.ParseInt(hex[4:6], 16, 32)
	return int(rv), int(gv), int(bv)
}

// RGBToHex formats 0-255 float component values as "#rrggbb", clamping and
// rounding the way Python's int() truncation does in rgb_to_hex.
func RGBToHex(r, g, b float64) string {
	clampByte := func(v float64) int {
		if v < 0 {
			v = 0
		}
		if v > 255 {
			v = 255
		}
		return int(v)
	}
	return fmt.Sprintf("#%02x%02x%02x", clampByte(r), clampByte(g), clampByte(b))
}

// GetLuminance computes relative sRGB luminance for 0-255 component values.
func GetLuminance(r, g, b int) float64 {
	adjust := func(v int) float64 {
		x := float64(v) / 255.0
		if x > 0.03928 {
			return math.Pow((x+0.055)/1.055, 2.4)
		}
		return x / 12.92
	}
	ar, ag, ab := adjust(r), adjust(g), adjust(b)
	return 0.2126*ar + 0.7152*ag + 0.0722*ab
}

// GetContrastRatio returns the WCAG contrast ratio between two hex colors.
func GetContrastRatio(hex1, hex2 string) float64 {
	r1, g1, b1 := HexToRGB(hex1)
	r2, g2, b2 := HexToRGB(hex2)
	l1 := GetLuminance(r1, g1, b1)
	l2 := GetLuminance(r2, g2, b2)
	if l1 > l2 {
		return (l1 + 0.05) / (l2 + 0.05)
	}
	return (l2 + 0.05) / (l1 + 0.05)
}

const (
	oneThird = 1.0 / 3.0
	oneSixth = 1.0 / 6.0
	twoThird = 2.0 / 3.0
)

// rgbToHLS ports Python's colorsys.rgb_to_hls for 0-1 float components.
func rgbToHLS(r, g, b float64) (h, l, s float64) {
	maxc := math.Max(r, math.Max(g, b))
	minc := math.Min(r, math.Min(g, b))
	sumc := maxc + minc
	rangec := maxc - minc
	l = sumc / 2.0
	if minc == maxc {
		return 0.0, l, 0.0
	}
	if l <= 0.5 {
		s = rangec / sumc
	} else {
		s = rangec / (2.0 - sumc)
	}
	rc := (maxc - r) / rangec
	gc := (maxc - g) / rangec
	bc := (maxc - b) / rangec
	switch maxc {
	case r:
		h = bc - gc
	case g:
		h = 2.0 + rc - bc
	default:
		h = 4.0 + gc - rc
	}
	h = math.Mod(h/6.0, 1.0)
	if h < 0 {
		h += 1.0
	}
	return h, l, s
}

func hlsV(m1, m2, hue float64) float64 {
	hue = math.Mod(hue, 1.0)
	if hue < 0 {
		hue += 1.0
	}
	switch {
	case hue < oneSixth:
		return m1 + (m2-m1)*hue*6.0
	case hue < 0.5:
		return m2
	case hue < twoThird:
		return m1 + (m2-m1)*(twoThird-hue)*6.0
	default:
		return m1
	}
}

// hlsToRGB ports Python's colorsys.hls_to_rgb for 0-1 float components.
func hlsToRGB(h, l, s float64) (r, g, b float64) {
	if s == 0.0 {
		return l, l, l
	}
	var m2 float64
	if l <= 0.5 {
		m2 = l * (1.0 + s)
	} else {
		m2 = l + s - (l * s)
	}
	m1 := 2.0*l - m2
	return hlsV(m1, m2, h+oneThird), hlsV(m1, m2, h), hlsV(m1, m2, h-oneThird)
}

// AdjustColorForContrast nudges fgHex's lightness towards bgHex's opposite
// end until it reaches minRatio contrast, matching adjust_color_for_contrast.
func AdjustColorForContrast(fgHex, bgHex string, minRatio float64) string {
	currentRatio := GetContrastRatio(fgHex, bgHex)
	if currentRatio >= minRatio {
		return fgHex
	}

	r, g, b := HexToRGB(fgHex)
	h, l, s := rgbToHLS(float64(r)/255.0, float64(g)/255.0, float64(b)/255.0)

	bgR, bgG, bgB := HexToRGB(bgHex)
	bgL := GetLuminance(bgR, bgG, bgB)

	direction := -1.0
	if bgL < 0.5 {
		direction = 1.0
	}

	const step = 0.05
	const maxSteps = 20

	bestHex := fgHex
	bestRatio := currentRatio

	for i := 0; i < maxSteps; i++ {
		l = math.Max(0.0, math.Min(1.0, l+step*direction))
		nr, ng, nb := hlsToRGB(h, l, s)
		newHex := RGBToHex(nr*255, ng*255, nb*255)
		newRatio := GetContrastRatio(newHex, bgHex)

		if newRatio > bestRatio {
			bestRatio = newRatio
			bestHex = newHex
		}
		if newRatio >= minRatio {
			return newHex
		}
	}

	return bestHex
}

// InvertLightness flips a color's HLS lightness (or sets it to targetL when
// non-nil), mirroring invert_lightness.
func InvertLightness(hexColor string, targetL *float64) string {
	r, g, b := HexToRGB(hexColor)
	h, l, s := rgbToHLS(float64(r)/255.0, float64(g)/255.0, float64(b)/255.0)

	newL := 1.0 - l
	if targetL != nil {
		newL = *targetL
	}

	nr, ng, nb := hlsToRGB(h, newL, s)
	return RGBToHex(nr*255, ng*255, nb*255)
}
