import { execSync, spawnSync } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { hexToRgb, Palette } from '../../colors';
import { config } from '../../config';
import { paletteToTokens, paletteToAccentTokens } from '../../core/themeTransform';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
  error: (m: string) => console.error('[daybreak]', m),
};

const KDE_COLORSCHEME_NAME = 'DaybreakTheme';

export class KDESystemAdapter {
  name = 'kde';

  getCurrentMode(): string {
    try {
      let result = spawnSync('kreadconfig6', ['--file', 'kdeglobals', '--group', 'General', '--key', 'ColorScheme'], { encoding: 'utf-8' });
      let scheme = (result.stdout || '').trim().toLowerCase();
      if (!scheme) {
        result = spawnSync('kreadconfig5', ['--file', 'kdeglobals', '--group', 'General', '--key', 'ColorScheme'], { encoding: 'utf-8' });
        scheme = (result.stdout || '').trim().toLowerCase();
      }
      return scheme.includes('dark') ? 'dark' : 'light';
    } catch (exc) {
      logger.error(`Failed to detect KDE mode: ${exc}`);
      return 'light';
    }
  }

  setMode(mode: string, palette?: Palette): void {
    if (palette) {
      this._writeKdeColorscheme(mode, palette);
    }

    const colorScheme = config.getSystemTheme('linux_kde', mode) || '';
    try {
      spawnSync('plasma-apply-colorscheme', [colorScheme], { stdio: 'ignore' });
      logger.info(`Applied KDE color scheme: ${colorScheme}`);
    } catch (exc) {
      logger.error(`Failed to apply color scheme ${colorScheme}`);
    }

    const plasmaTheme = mode === 'dark' ? 'breath-dark' : 'breath-light';
    const plasmaResult = spawnSync('plasma-apply-desktoptheme', [plasmaTheme], { stdio: 'ignore' });
    if (plasmaResult.error) {
      try {
        spawnSync('kwriteconfig6', ['--file', 'plasmarc', '--group', 'Theme', '--key', 'name', plasmaTheme], { stdio: 'ignore' });
        logger.info(`Set plasmarc theme to ${plasmaTheme}`);
      } catch (exc) {
        logger.error(`Failed to update plasmarc: ${exc}`);
      }
    }
  }

  private _writeKdeColorscheme(mode: string, palette: Palette): void {
    try {
      const tokens = paletteToTokens(palette, mode);
      const accentTokens = paletteToAccentTokens(palette, mode);
      const schemeDir = path.join(os.homedir(), '.local', 'share', 'color-schemes');
      fs.mkdirSync(schemeDir, { recursive: true });
      const schemePath = path.join(schemeDir, `${KDE_COLORSCHEME_NAME}.colors`);
      const content = buildKdeColorscheme(tokens, accentTokens);
      fs.writeFileSync(schemePath, content, 'utf-8');
      logger.info(`Wrote KDE colorscheme: ${schemePath}`);
    } catch (exc) {
      logger.warn(`Failed to write KDE colorscheme: ${exc}`);
    }
  }
}

function rgb(hexColor: string): string {
  const [r, g, b] = hexToRgb(hexColor);
  return `${r},${g},${b}`;
}

function buildKdeColorscheme(tokens: Record<string, string>, accentTokens: Record<string, string>): string {
  const bg = tokens['bg'];
  const fg = tokens['fg'];
  const muted = tokens['muted'];
  const primary = tokens['primary'];
  const success = tokens['success'];
  const warning = tokens['warning'];
  const error = tokens['error'];
  const info = tokens['info'];
  const surface1 = tokens['surface_1'];
  const surface2 = tokens['surface_2'];
  const accent = accentTokens['accent_primary'];
  const accentSelection = accentTokens['accent_selection'];

  function colorGroup(bgNormal: string, bgAlt: string, fgNormal: string, fgInactive: string, active: string, link: string, negative: string, neutral: string, positive: string, visited: string, deco: string): string {
    return [
      `BackgroundAlternate=${rgb(bgAlt)}`,
      `BackgroundNormal=${rgb(bgNormal)}`,
      `DecorationFocus=${rgb(deco)}`,
      `DecorationHover=${rgb(deco)}`,
      `ForegroundActive=${rgb(active)}`,
      `ForegroundInactive=${rgb(fgInactive)}`,
      `ForegroundLink=${rgb(link)}`,
      `ForegroundNegative=${rgb(negative)}`,
      `ForegroundNeutral=${rgb(neutral)}`,
      `ForegroundNormal=${rgb(fgNormal)}`,
      `ForegroundPositive=${rgb(positive)}`,
      `ForegroundVisited=${rgb(visited)}`,
    ].join('\n') + '\n';
  }

  const windowGroup = colorGroup(surface1, surface2, fg, muted, accent, info, error, warning, success, primary, accent);
  const buttonGroup = colorGroup(surface1, surface2, fg, muted, accent, info, error, warning, success, primary, accent);
  const viewGroup = colorGroup(bg, surface1, fg, muted, accent, info, error, warning, success, primary, accent);
  const selectionGroup = colorGroup(accent, accentSelection, bg, muted, accent, info, error, warning, success, primary, accent);
  const tooltipGroup = colorGroup(surface1, surface2, fg, muted, accent, info, error, warning, success, primary, accent);
  const headerGroup = colorGroup(surface2, surface1, fg, muted, accent, info, error, warning, success, primary, accent);

  return [
    '[ColorEffects:Disabled]',
    'Color=56,56,56',
    'ColorAmount=0',
    'ColorEffect=0',
    'ContrastAmount=0.65',
    'ContrastEffect=1',
    'IntensityAmount=0.1',
    'IntensityEffect=2',
    '',
    '[ColorEffects:Inactive]',
    'ChangeSelectionColor=true',
    `Color=${rgb(muted)}`,
    'ColorAmount=0.025',
    'ColorEffect=2',
    'ContrastAmount=0.1',
    'ContrastEffect=2',
    'Enable=false',
    'IntensityAmount=0',
    'IntensityEffect=0',
    '',
    '[Colors:Button]',
    buttonGroup,
    '[Colors:Complementary]',
    viewGroup,
    '[Colors:Header]',
    headerGroup,
    '[Colors:Selection]',
    selectionGroup,
    '[Colors:Tooltip]',
    tooltipGroup,
    '[Colors:View]',
    viewGroup,
    '[Colors:Window]',
    windowGroup,
    '[General]',
    `ColorScheme=${KDE_COLORSCHEME_NAME}`,
    'Name=Daybreak Theme',
    'shadeSortColumn=true',
    '',
    '[KDE]',
    'contrast=4',
    '',
    '[WM]',
    `activeBackground=${rgb(surface1)}`,
    `activeForeground=${rgb(fg)}`,
    `inactiveBackground=${rgb(bg)}`,
    `inactiveForeground=${rgb(muted)}`,
    '',
  ].join('\n');
}
