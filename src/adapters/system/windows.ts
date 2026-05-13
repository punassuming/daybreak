import { execSync } from 'child_process';
import { Palette } from '../../colors';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
  error: (m: string) => console.error('[daybreak]', m),
};

export class WindowsSystemAdapter {
  name = 'windows';

  getCurrentMode(): string {
    if (process.platform !== 'win32') return 'light';
    try {
      const output = execSync(
        'reg query "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize" /v AppsUseLightTheme',
        { encoding: 'utf-8' },
      );
      const match = output.match(/AppsUseLightTheme\s+REG_DWORD\s+(0x[0-9a-fA-F]+)/);
      if (match) {
        return parseInt(match[1], 16) === 1 ? 'light' : 'dark';
      }
      return 'light';
    } catch (exc) {
      logger.error(`Failed to read Windows registry: ${exc}`);
      return 'light';
    }
  }

  setMode(mode: string, palette?: Palette): void {
    if (process.platform !== 'win32') {
      logger.warn('Not running on Windows, skipping registry changes.');
      return;
    }
    try {
      const value = mode === 'light' ? '1' : '0';
      const keyPath = 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize';
      execSync(`reg add "${keyPath}" /v AppsUseLightTheme /t REG_DWORD /d ${value} /f`);
      execSync(`reg add "${keyPath}" /v SystemUsesLightTheme /t REG_DWORD /d ${value} /f`);
      logger.info(`Registry updated for ${mode} mode.`);
    } catch (exc) {
      logger.error(`Failed to change Windows theme: ${exc}`);
    }
  }
}
