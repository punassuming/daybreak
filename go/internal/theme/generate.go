package theme

import "math"

func floatPtr(v float64) *float64 { return &v }

// GenerateLightFromDark mirrors colors.generate_light_from_dark.
func GenerateLightFromDark(darkPalette Palette) Palette {
	light := Palette{Special: map[string]string{}, Colors: map[string]string{}}

	bgOrig := darkPalette.Special["background"]
	light.Special["background"] = InvertLightness(bgOrig, floatPtr(0.96))
	bgHex := light.Special["background"]

	fgOrig := darkPalette.Special["foreground"]
	fgCandidate := InvertLightness(fgOrig, floatPtr(0.15))
	light.Special["foreground"] = AdjustColorForContrast(fgCandidate, bgHex, 7.0)
	light.Special["cursor"] = light.Special["foreground"]

	for i, color := range darkPalette.Colors {
		r, g, b := HexToRGB(color)
		h, l, s := rgbToHLS(float64(r)/255.0, float64(g)/255.0, float64(b)/255.0)

		newL := math.Max(0.2, math.Min(0.45, l*0.5))
		newS := math.Min(1.0, s*1.1)

		if i == "3" || i == "11" {
			newL = math.Max(0.2, math.Min(0.35, l*0.4))
			newS = math.Min(1.0, s*1.3)
			if h > 0.14 && h < 0.18 {
				h = 0.10
			}
		}

		rr, rg, rb := hlsToRGB(h, newL, newS)
		rawHex := RGBToHex(rr*255, rg*255, rb*255)

		light.Colors[i] = AdjustColorForContrast(rawHex, bgHex, 4.0)
	}

	light.Colors["0"] = AdjustColorForContrast(light.Colors["0"], light.Colors["3"], 4.5)
	light.Colors["15"] = "#ffffff"

	return light
}

// GenerateDarkFromLight mirrors colors.generate_dark_from_light.
func GenerateDarkFromLight(lightPalette Palette) Palette {
	dark := Palette{Special: map[string]string{}, Colors: map[string]string{}}

	bgOrig := lightPalette.Special["background"]
	dark.Special["background"] = InvertLightness(bgOrig, floatPtr(0.10))
	bgHex := dark.Special["background"]

	fgOrig := lightPalette.Special["foreground"]
	fgCandidate := InvertLightness(fgOrig, floatPtr(0.85))
	dark.Special["foreground"] = AdjustColorForContrast(fgCandidate, bgHex, 7.0)
	dark.Special["cursor"] = dark.Special["foreground"]

	for i, color := range lightPalette.Colors {
		r, g, b := HexToRGB(color)
		h, l, s := rgbToHLS(float64(r)/255.0, float64(g)/255.0, float64(b)/255.0)

		newL := math.Min(0.85, math.Max(0.6, l*2.0))

		rr, rg, rb := hlsToRGB(h, newL, s)
		rawHex := RGBToHex(rr*255, rg*255, rb*255)

		dark.Colors[i] = AdjustColorForContrast(rawHex, bgHex, 4.0)
	}

	return dark
}
