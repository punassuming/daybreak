import * as fs from 'fs';
import * as path from 'path';
import { config } from '../../config';
import { Palette } from '../../colors';
import { loadJsoncFile, dumpJsonFile } from './jsonc';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
};

export class WindowsTerminalAdapter {
  name = 'windows_terminal';

  applyMode(mode: string, _themeName: string, _palette?: Palette): void {
    if (process.platform !== 'win32') return;

    const targetScheme = config.get(
      'integrations',
      `windows_terminal_${mode}_scheme`,
      mode === 'light' ? 'One Half Light' : 'One Half Dark',
    );

    for (const settingsPath of iterWindowsTerminalSettings()) {
      this._applyScheme(settingsPath, targetScheme);
    }
  }

  private _applyScheme(filePath: string, targetScheme: string): void {
    let data: any;
    try {
      data = loadJsoncFile(filePath);
    } catch (exc) {
      logger.warn(`Windows Terminal: Failed to parse ${filePath}: ${exc}`);
      return;
    }

    let changed = false;
    if (!data.profiles) data.profiles = {};
    if (!data.profiles.defaults) data.profiles.defaults = {};
    if (data.profiles.defaults.colorScheme !== targetScheme) {
      data.profiles.defaults.colorScheme = targetScheme;
      changed = true;
    }

    const profileList = data.profiles.list;
    if (Array.isArray(profileList)) {
      for (const entry of profileList) {
        if (entry && typeof entry === 'object' && 'colorScheme' in entry) {
          if (entry.colorScheme !== targetScheme) {
            entry.colorScheme = targetScheme;
            changed = true;
          }
        }
      }
    }

    if (changed) {
      try {
        dumpJsonFile(filePath, data);
        logger.info(`Windows Terminal: Applied colorScheme '${targetScheme}' to ${filePath}`);
      } catch (exc) {
        logger.warn(`Windows Terminal: Failed writing ${filePath}: ${exc}`);
      }
    }
  }
}

function iterWindowsTerminalSettings(): string[] {
  const localAppData = process.env['LOCALAPPDATA'];
  if (!localAppData) return [];

  const results: string[] = [];
  const seen = new Set<string>();

  const packagedRoot = path.join(localAppData, 'Packages');
  if (fs.existsSync(packagedRoot)) {
    try {
      for (const entry of fs.readdirSync(packagedRoot)) {
        if (!entry.startsWith('Microsoft.WindowsTerminal')) continue;
        const candidate = path.join(packagedRoot, entry, 'LocalState', 'settings.json');
        if (fs.existsSync(candidate) && !seen.has(candidate)) {
          results.push(candidate);
          seen.add(candidate);
        }
      }
    } catch { /* ignore */ }
  }

  const unpackaged = path.join(localAppData, 'Microsoft', 'Windows Terminal', 'settings.json');
  if (fs.existsSync(unpackaged) && !seen.has(unpackaged)) {
    results.push(unpackaged);
  }

  return results;
}
