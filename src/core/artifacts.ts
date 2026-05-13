import * as fs from 'fs';
import * as path from 'path';
import { hexToRgb } from '../colors';

const logger = { warn: (m: string) => console.warn('[daybreak]', m), debug: (m: string) => {} };

export function generateArtifacts(
  configDir: string,
  themeName: string,
  mode: string,
  tokens: Record<string, string>,
  accentTokens: Record<string, string>,
  palette: object,
): void {
  try {
    fs.mkdirSync(configDir, { recursive: true });
    writePaletteJson(configDir, themeName, mode, tokens, accentTokens, palette);
    writeEnvSh(configDir, themeName, mode, tokens, accentTokens);
    writeLsColors(configDir, mode, tokens);
  } catch (exc) {
    logger.warn(`Failed to write theme artifacts: ${exc}`);
  }
}

function writePaletteJson(
  configDir: string,
  themeName: string,
  mode: string,
  tokens: Record<string, string>,
  accentTokens: Record<string, string>,
  palette: any,
): void {
  const data = {
    theme: themeName,
    mode,
    tokens,
    accent_tokens: accentTokens,
    palette: {
      special: palette.special || {},
      colors: Object.fromEntries(
        Object.entries(palette.colors || {}).filter(([, v]) => typeof v === 'string'),
      ),
    },
  };
  const filePath = path.join(configDir, 'palette.json');
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

function writeEnvSh(
  configDir: string,
  themeName: string,
  mode: string,
  tokens: Record<string, string>,
  accentTokens: Record<string, string>,
): void {
  const lines = [
    '# Daybreak theme environment — auto-generated, do not edit manually',
    `DAYBREAK_THEME="${themeName}"`,
    `DAYBREAK_MODE="${mode}"`,
    `DAYBREAK_COLOR_BG="${tokens['bg']}"`,
    `DAYBREAK_COLOR_FG="${tokens['fg']}"`,
    `DAYBREAK_COLOR_PRIMARY="${tokens['primary']}"`,
    `DAYBREAK_COLOR_SUCCESS="${tokens['success']}"`,
    `DAYBREAK_COLOR_WARNING="${tokens['warning']}"`,
    `DAYBREAK_COLOR_ERROR="${tokens['error']}"`,
    `DAYBREAK_COLOR_INFO="${tokens['info']}"`,
    `DAYBREAK_ACCENT_PRIMARY="${accentTokens['accent_primary']}"`,
    `DAYBREAK_ACCENT_SECONDARY="${accentTokens['accent_secondary']}"`,
    `DAYBREAK_ACCENT_SUCCESS="${accentTokens['accent_success']}"`,
    `DAYBREAK_ACCENT_WARNING="${accentTokens['accent_warning']}"`,
    `DAYBREAK_ACCENT_ERROR="${accentTokens['accent_error']}"`,
    `DAYBREAK_ACCENT_SELECTION="${accentTokens['accent_selection']}"`,
    'export DAYBREAK_THEME DAYBREAK_MODE',
    'export DAYBREAK_COLOR_BG DAYBREAK_COLOR_FG DAYBREAK_COLOR_PRIMARY',
    'export DAYBREAK_COLOR_SUCCESS DAYBREAK_COLOR_WARNING DAYBREAK_COLOR_ERROR DAYBREAK_COLOR_INFO',
    'export DAYBREAK_ACCENT_PRIMARY DAYBREAK_ACCENT_SECONDARY DAYBREAK_ACCENT_SUCCESS',
    'export DAYBREAK_ACCENT_WARNING DAYBREAK_ACCENT_ERROR DAYBREAK_ACCENT_SELECTION',
  ];
  fs.writeFileSync(path.join(configDir, 'env.sh'), lines.join('\n') + '\n', 'utf-8');
}

function fgAnsi(hexColor: string): string {
  const [r, g, b] = hexToRgb(hexColor);
  return `38;2;${r};${g};${b}`;
}

function writeLsColors(
  configDir: string,
  mode: string,
  tokens: Record<string, string>,
): void {
  const entries: Record<string, string> = {
    di: `1;${fgAnsi(tokens['primary'])}`,
    ln: fgAnsi(tokens['info']),
    ex: fgAnsi(tokens['success']),
    pi: fgAnsi(tokens['warning']),
    so: fgAnsi(tokens['info']),
    bd: fgAnsi(tokens['warning']),
    cd: fgAnsi(tokens['warning']),
    or: fgAnsi(tokens['error']),
    mi: fgAnsi(tokens['error']),
    '*.tar': `1;${fgAnsi(tokens['error'])}`,
    '*.tgz': `1;${fgAnsi(tokens['error'])}`,
    '*.gz': `1;${fgAnsi(tokens['error'])}`,
    '*.bz2': `1;${fgAnsi(tokens['error'])}`,
    '*.xz': `1;${fgAnsi(tokens['error'])}`,
    '*.zip': `1;${fgAnsi(tokens['error'])}`,
    '*.7z': `1;${fgAnsi(tokens['error'])}`,
    '*.py': fgAnsi(tokens['primary']),
    '*.sh': fgAnsi(tokens['success']),
    '*.bash': fgAnsi(tokens['success']),
    '*.zsh': fgAnsi(tokens['success']),
    '*.fish': fgAnsi(tokens['success']),
    '*.json': fgAnsi(tokens['warning']),
    '*.toml': fgAnsi(tokens['warning']),
    '*.yaml': fgAnsi(tokens['warning']),
    '*.yml': fgAnsi(tokens['warning']),
    '*.ini': fgAnsi(tokens['warning']),
    '*.cfg': fgAnsi(tokens['warning']),
    '*.md': fgAnsi(tokens['info']),
    '*.rst': fgAnsi(tokens['info']),
    '*.txt': fgAnsi(tokens['muted']),
  };

  const lsColorsValue = Object.entries(entries)
    .map(([k, v]) => `${k}=${v}`)
    .join(':');

  const lines = [
    '# Daybreak LS_COLORS — auto-generated, do not edit manually',
    '# Source this file to apply terminal file-type colours:',
    '#   [ -f "$HOME/.config/daybreak/ls_colors.sh" ] && . "$HOME/.config/daybreak/ls_colors.sh"',
    `LS_COLORS="${lsColorsValue}"`,
    'export LS_COLORS',
  ];
  fs.writeFileSync(path.join(configDir, 'ls_colors.sh'), lines.join('\n') + '\n', 'utf-8');
}
