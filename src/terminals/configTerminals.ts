import * as fs from 'fs';
import * as path from 'path';
import { Terminal } from './base';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
  error: (m: string) => console.error('[daybreak]', m),
};

export class BaseConfigTerminal extends Terminal {
  protected termName: string;
  protected configDir: string;
  protected themeFile: string;
  protected darkSrc: string;
  protected lightSrc: string;

  constructor(
    termName: string,
    configDir: string,
    themeFileName = 'theme.conf',
    darkSrc = 'dark.conf',
    lightSrc = 'light.conf',
  ) {
    super();
    this.termName = termName;
    this.configDir = configDir.replace(/^~/, require('os').homedir());
    this.themeFile = path.join(this.configDir, themeFileName);
    this.darkSrc = path.join(this.configDir, 'themes', darkSrc);
    this.lightSrc = path.join(this.configDir, 'themes', lightSrc);
  }

  setMode(mode: string): void {
    if (!fs.existsSync(this.configDir)) return;

    const src = mode === 'dark' ? this.darkSrc : this.lightSrc;
    if (!fs.existsSync(src)) {
      logger.warn(`${this.termName}: Theme source file ${src} does not exist. Skipping.`);
      return;
    }

    try {
      fs.mkdirSync(path.dirname(this.themeFile), { recursive: true });
      fs.copyFileSync(src, this.themeFile);
      logger.info(`${this.termName}: Updated ${this.themeFile} to ${mode} mode.`);
      this.reloadConfig();
    } catch (e) {
      logger.error(`${this.termName}: Failed to update config: ${e}`);
    }
  }

  protected reloadConfig(): void {
    // override in subclass if needed
  }
}

export class Ghostty extends BaseConfigTerminal {
  constructor() {
    super('Ghostty', '~/.config/ghostty', 'theme', 'dark', 'light');
  }
}

export class WezTerm extends BaseConfigTerminal {
  constructor() {
    super('WezTerm', '~/.config/wezterm', 'theme.lua', 'dark.lua', 'light.lua');
  }
}
