export const THEME_MODES: Set<string> = new Set(['light', 'dark']);

export const TOKEN_KEYS: readonly string[] = [
  'bg',
  'fg',
  'cursor',
  'muted',
  'primary',
  'success',
  'warning',
  'error',
  'info',
  'surface_1',
  'surface_2',
  'surface_3',
] as const;

export const ACCENT_KEYS: readonly string[] = [
  'accent_primary',
  'accent_secondary',
  'accent_success',
  'accent_warning',
  'accent_error',
  'accent_selection',
] as const;

export function normalizeMode(mode: string): string {
  const normalized = (mode || '').trim().toLowerCase();
  if (!THEME_MODES.has(normalized)) {
    throw new Error(`Unsupported mode '${mode}'. Expected one of: ${[...THEME_MODES].sort().join(', ')}`);
  }
  return normalized;
}

export function isHexColor(value: string): boolean {
  if (typeof value !== 'string') return false;
  if (value.length !== 7 || !value.startsWith('#')) return false;
  try {
    parseInt(value.slice(1), 16);
    return true;
  } catch {
    return false;
  }
}

export function validateTokens(tokens: Record<string, string>): void {
  const missing = TOKEN_KEYS.filter(key => !(key in tokens));
  if (missing.length > 0) {
    throw new Error(`Theme tokens missing required keys: ${JSON.stringify(missing)}`);
  }
  const invalid = Object.entries(tokens)
    .filter(([key, value]) => TOKEN_KEYS.includes(key) && !isHexColor(value))
    .map(([key]) => key);
  if (invalid.length > 0) {
    throw new Error(`Theme tokens contain invalid hex colors for keys: ${JSON.stringify(invalid)}`);
  }
}
