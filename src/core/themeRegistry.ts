import { Palette } from '../colors';
import { THEME_LIBRARY, getThemePalette } from '../themes';
import { normalizeMode, validateTokens } from './themeModel';
import { paletteToTokens, paletteToAccentTokens } from './themeTransform';

export class ThemeRegistry {
  listThemes(): string[] {
    return Object.keys(THEME_LIBRARY).sort();
  }

  getPalette(themeName: string, mode: string): Palette {
    const normalizedMode = normalizeMode(mode);
    const paletteSet = getThemePalette(themeName);
    const palette = paletteSet[normalizedMode as 'light' | 'dark'];
    if (!palette) {
      throw new Error(`Theme '${themeName}' does not provide mode '${normalizedMode}'.`);
    }
    return palette;
  }

  getTokens(themeName: string, mode: string): Record<string, string> {
    const palette = this.getPalette(themeName, mode);
    const tokens = paletteToTokens(palette, mode);
    validateTokens(tokens);
    return tokens;
  }

  getAccentTokens(themeName: string, mode: string): Record<string, string> {
    const palette = this.getPalette(themeName, mode);
    return paletteToAccentTokens(palette, mode);
  }

  getTheme(themeName: string, mode: string): object {
    const normalizedMode = normalizeMode(mode);
    const tokens = this.getTokens(themeName, normalizedMode);
    const accentTokens = this.getAccentTokens(themeName, normalizedMode);
    const palette = this.getPalette(themeName, normalizedMode);
    return {
      id: themeName.toLowerCase().replace(/ /g, '-'),
      name: themeName,
      mode: normalizedMode,
      tokens,
      accent_tokens: accentTokens,
      palette,
    };
  }
}
