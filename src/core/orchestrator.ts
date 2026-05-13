import { config } from '../config';
import { generateArtifacts } from './artifacts';
import { normalizeMode } from './themeModel';
import { ThemeRegistry } from './themeRegistry';
import { Palette } from '../colors';

const logger = {
  warn: (m: string) => console.warn('[daybreak]', m),
  debug: (m: string) => {},
};

export interface SystemAdapter {
  name: string;
  getCurrentMode(): string;
  setMode(mode: string, palette?: Palette): void;
}

export interface TerminalAdapter {
  name: string;
  applyMode(mode: string, themeName: string, palette?: Palette): void;
}

export class ThemeOrchestrator {
  private systemAdapter: SystemAdapter | null;
  private terminalAdapters: TerminalAdapter[];
  private registry: ThemeRegistry;

  constructor(
    systemAdapter?: SystemAdapter | null,
    terminalAdapters?: TerminalAdapter[],
    registry?: ThemeRegistry,
  ) {
    this.systemAdapter = systemAdapter || null;
    this.terminalAdapters = terminalAdapters || [];
    this.registry = registry || new ThemeRegistry();
  }

  getCurrentMode(): string {
    if (!this.systemAdapter) return 'light';
    try {
      return normalizeMode(this.systemAdapter.getCurrentMode());
    } catch (exc) {
      logger.warn(`Failed to detect current mode. Defaulting to light: ${exc}`);
      return 'light';
    }
  }

  apply(mode: string, themeName?: string): string {
    config.reload();
    const normalizedMode = normalizeMode(mode);
    const resolvedTheme = themeName || config.getModeThemeName(normalizedMode);
    const palette = this.registry.getPalette(resolvedTheme, normalizedMode);

    if (this.systemAdapter) {
      this.systemAdapter.setMode(normalizedMode, palette);
    }

    for (const adapter of this.terminalAdapters) {
      try {
        adapter.applyMode(normalizedMode, resolvedTheme, palette);
      } catch (exc) {
        const name = adapter.name || adapter.constructor.name;
        logger.warn(`Terminal adapter '${name}' failed: ${exc}`);
      }
    }

    try {
      const tokens = this.registry.getTokens(resolvedTheme, normalizedMode);
      const accentTokens = this.registry.getAccentTokens(resolvedTheme, normalizedMode);
      generateArtifacts(config.configDir, resolvedTheme, normalizedMode, tokens, accentTokens, palette);
    } catch (exc) {
      logger.warn(`Failed to generate theme artifacts: ${exc}`);
    }

    return resolvedTheme;
  }

  applyToggle(explicitThemeName?: string): [string, string] {
    const targetMode = this.getCurrentMode() === 'dark' ? 'light' : 'dark';
    const themeName = this.apply(targetMode, explicitThemeName);
    return [targetMode, themeName];
  }
}
