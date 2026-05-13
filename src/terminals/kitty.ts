import { spawnSync } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { Terminal } from './base';

export class Kitty extends Terminal {
  setMode(mode: string): void {
    const configDir = path.join(os.homedir(), '.config', 'kitty');
    const themeLink = path.join(configDir, 'current-theme.conf');
    const darkSrc = path.join(configDir, 'themes', 'dark.conf');
    const lightSrc = path.join(configDir, 'themes', 'light.conf');
    const src = mode === 'dark' ? darkSrc : lightSrc;

    if (fs.existsSync(src)) {
      try {
        if (fs.existsSync(themeLink) || fs.lstatSync(themeLink).isSymbolicLink?.()) {
          fs.unlinkSync(themeLink);
        }
        fs.symlinkSync(src, themeLink);
      } catch {
        // best-effort
      }
    }

    try {
      spawnSync('pkill', ['-USR1', 'kitty'], { stdio: 'ignore' });
    } catch {
      // ignore
    }
  }
}
