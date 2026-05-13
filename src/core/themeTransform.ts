import { adjustColorForContrast, Palette } from '../colors';

function fallback(value: string | undefined, def: string): string {
  return value || def;
}

export function paletteToTokens(palette: Palette, mode: string): Record<string, string> {
  const special = palette.special || { background: '', foreground: '', cursor: '' };
  const colors = palette.colors || {};

  const bg = fallback(special.background, mode === 'dark' ? '#111111' : '#f5f5f5');
  const fg = fallback(special.foreground, mode === 'dark' ? '#e5e5e5' : '#121212');
  const cursor = fallback(special.cursor, fg);

  const muted = fallback(colors['8'], fg);
  const primary = fallback(colors['4'], fg);
  const success = fallback(colors['2'], fg);
  const warning = fallback(colors['3'], fg);
  const error = fallback(colors['1'], fg);
  const info = fallback(colors['6'], primary);

  const surface1 = fallback(colors['18'], bg);
  const surface2 = fallback(colors['19'], surface1);
  const surface3 = fallback(colors['20'], muted);

  const tokens: Record<string, string> = {
    bg,
    fg,
    cursor,
    muted,
    primary,
    success,
    warning,
    error,
    info,
    surface_1: surface1,
    surface_2: surface2,
    surface_3: surface3,
  };

  for (const key of ['fg', 'muted', 'primary', 'success', 'warning', 'error', 'info']) {
    tokens[key] = adjustColorForContrast(tokens[key], bg, 4.0);
  }

  return tokens;
}

export function paletteToAccentTokens(palette: Palette, mode: string): Record<string, string> {
  const special = palette.special || { background: '', foreground: '', cursor: '' };
  const colors = palette.colors || {};

  const bg = fallback(special.background, mode === 'dark' ? '#111111' : '#f5f5f5');

  const accentPrimary = fallback(colors['4'], fallback(special.foreground, bg));
  const accentSecondary = fallback(colors['5'], accentPrimary);
  const accentSuccess = fallback(colors['2'], fallback(special.foreground, bg));
  const accentWarning = fallback(colors['3'], accentPrimary);
  const accentError = fallback(colors['1'], accentPrimary);
  const accentSelection = fallback(colors['18'], bg);

  const accents: Record<string, string> = {
    accent_primary: accentPrimary,
    accent_secondary: accentSecondary,
    accent_success: accentSuccess,
    accent_warning: accentWarning,
    accent_error: accentError,
    accent_selection: accentSelection,
  };

  for (const key of ['accent_primary', 'accent_secondary', 'accent_success', 'accent_warning', 'accent_error']) {
    accents[key] = adjustColorForContrast(accents[key], bg, 3.0);
  }

  return accents;
}
