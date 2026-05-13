import * as fs from 'fs';
import * as path from 'path';
import { config } from '../../config';
import { Palette } from '../../colors';
import { loadJsoncFile, dumpJsonFile } from './jsonc';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
  debug: (m: string) => {},
};

export class ObsidianAdapter {
  name = 'obsidian';

  applyMode(mode: string, _themeName: string, _palette?: Palette): void {
    if (process.platform !== 'win32') return;

    const appData = process.env['APPDATA'];
    if (!appData) return;

    const targetTheme = config.get(
      'integrations',
      `obsidian_${mode}_theme`,
      mode === 'light' ? 'moonstone' : 'obsidian',
    );

    const globalPath = path.join(appData, 'obsidian', 'obsidian.json');
    if (!fs.existsSync(globalPath)) {
      logger.debug('Obsidian: global settings file not found, skipping.');
      return;
    }

    let vaultPaths: string[] = [];
    try {
      const globalData = loadJsoncFile(globalPath);
      let changed = false;
      if (globalData && typeof globalData === 'object') {
        if (globalData.theme !== targetTheme) {
          globalData.theme = targetTheme;
          changed = true;
        }
        vaultPaths = extractVaultPaths(globalData);
      }
      if (changed) {
        dumpJsonFile(globalPath, globalData);
        logger.info(`Obsidian: Applied theme '${targetTheme}' to ${globalPath}`);
      }
    } catch (exc) {
      logger.warn(`Obsidian: Failed to update ${globalPath}: ${exc}`);
    }

    for (const vaultPath of vaultPaths) {
      const appJson = path.join(vaultPath, '.obsidian', 'app.json');
      if (!fs.existsSync(appJson)) continue;
      try {
        const appJsonData = loadJsoncFile(appJson);
        if (!appJsonData || typeof appJsonData !== 'object') continue;
        if (appJsonData.theme === targetTheme) continue;
        appJsonData.theme = targetTheme;
        dumpJsonFile(appJson, appJsonData);
        logger.info(`Obsidian: Applied theme '${targetTheme}' to ${appJson}`);
      } catch (exc) {
        logger.warn(`Obsidian: Failed to update ${appJson}: ${exc}`);
      }
    }
  }
}

function extractVaultPaths(globalData: any): string[] {
  const vaults = globalData.vaults;
  if (!vaults || typeof vaults !== 'object') return [];
  const results: string[] = [];
  for (const entry of Object.values(vaults)) {
    if (!entry || typeof entry !== 'object') continue;
    const pathValue = (entry as any).path;
    if (typeof pathValue === 'string' && pathValue && fs.existsSync(pathValue)) {
      results.push(pathValue);
    }
  }
  return results;
}
