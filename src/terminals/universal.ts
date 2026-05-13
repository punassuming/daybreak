import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { getThemePalette } from '../themes';
import { config } from '../config';
import { Terminal } from './base';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
};

export class UniversalPty extends Terminal {
  setMode(mode: string): void {
    const themeName = config.getTerminalThemeName(mode);
    this.applyTheme(themeName, mode);
  }

  applyTheme(themeName: string, mode: string): void {
    const paletteSet = getThemePalette(themeName);
    const theme = paletteSet[mode as 'light' | 'dark'];
    if (!theme) {
      logger.warn(`Theme '${themeName}' does not support ${mode} mode.`);
      return;
    }

    const sequences: string[] = [];
    sequences.push(`\x1b]10;${theme.special.foreground}\x07`);
    sequences.push(`\x1b]11;${theme.special.background}\x07`);
    sequences.push(`\x1b]12;${theme.special.cursor}\x07`);

    for (const [i, color] of Object.entries(theme.colors)) {
      sequences.push(`\x1b]4;${i};${color}\x07`);
    }

    const fullPayload = sequences.join('');
    this._broadcast(fullPayload);
    this._writeShellScript(fullPayload);
  }

  private _broadcast(payload: string): void {
    if (process.platform === 'win32') return;
    const { readdirSync } = fs;
    let count = 0;
    try {
      const ptys = readdirSync('/dev/pts').filter(f => /^\d+$/.test(f));
      for (const pty of ptys) {
        const ptyPath = `/dev/pts/${pty}`;
        try {
          const fd = fs.openSync(ptyPath, fs.constants.O_WRONLY | fs.constants.O_NOCTTY);
          fs.writeSync(fd, payload);
          fs.closeSync(fd);
          count++;
        } catch {
          // ignore permission errors
        }
      }
    } catch {
      // /dev/pts may not exist
    }
    if (count > 0) logger.info(`Broadcasted palette to ${count} terminals.`);
  }

  private _writeShellScript(payload: string): void {
    const configDir = config.configDir;
    try {
      fs.mkdirSync(configDir, { recursive: true });
    } catch { return; }

    try {
      fs.writeFileSync(path.join(configDir, 'theme.sh'), `#!/bin/sh\nprintf '${payload}'\n`);
    } catch (e) {
      logger.warn(`Failed to write theme.sh: ${e}`);
    }

    try {
      fs.writeFileSync(path.join(configDir, 'theme.fish'), `printf '${payload}'\n`);
    } catch (e) {
      logger.warn(`Failed to write theme.fish: ${e}`);
    }

    try {
      const psSafe = payload.replace(/\x1b/g, '$([char]0x1b)');
      fs.writeFileSync(path.join(configDir, 'theme.ps1'), `Write-Host "${psSafe}" -NoNewline\n`);
    } catch (e) {
      logger.warn(`Failed to write theme.ps1: ${e}`);
    }
  }
}
