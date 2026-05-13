import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { Terminal } from './base';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
  error: (m: string) => console.error('[daybreak]', m),
};

function parseIni(text: string): Record<string, Record<string, string>> {
  const result: Record<string, Record<string, string>> = {};
  let currentSection = '';
  for (const raw of text.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#') || line.startsWith(';')) continue;
    const sectionMatch = line.match(/^\[(.+)\]$/);
    if (sectionMatch) {
      currentSection = sectionMatch[1];
      if (!result[currentSection]) result[currentSection] = {};
      continue;
    }
    const eqIdx = line.indexOf('=');
    if (eqIdx !== -1 && currentSection) {
      const key = line.slice(0, eqIdx).trim();
      const value = line.slice(eqIdx + 1).trim();
      result[currentSection][key] = value;
    }
  }
  return result;
}

function dumpIni(data: Record<string, Record<string, string>>): string {
  const lines: string[] = [];
  for (const [section, entries] of Object.entries(data)) {
    lines.push(`[${section}]`);
    for (const [key, value] of Object.entries(entries)) {
      lines.push(`${key}=${value}`);
    }
    lines.push('');
  }
  return lines.join('\n');
}

export class Konsole extends Terminal {
  setMode(mode: string): void {
    const configPath = path.join(os.homedir(), '.config', 'konsolerc');
    if (!fs.existsSync(configPath)) return;

    try {
      const text = fs.readFileSync(configPath, 'utf-8');
      const konsolerc = parseIni(text);

      let defaultProfileName = 'Default';
      const desktopEntry = konsolerc['Desktop Entry'];
      if (desktopEntry && desktopEntry['DefaultProfile']) {
        defaultProfileName = desktopEntry['DefaultProfile'];
      }

      let profilePath = path.join(os.homedir(), '.local', 'share', 'konsole', defaultProfileName);
      if (!profilePath.endsWith('.profile')) profilePath += '.profile';

      if (!fs.existsSync(profilePath)) {
        logger.warn(`Konsole profile ${profilePath} not found.`);
        return;
      }

      const profileText = fs.readFileSync(profilePath, 'utf-8');
      const profile = parseIni(profileText);
      const targetScheme = mode === 'light' ? 'Breeze' : 'BreezeDark';

      if (!profile['Appearance']) profile['Appearance'] = {};
      profile['Appearance']['ColorScheme'] = targetScheme;

      fs.writeFileSync(profilePath, dumpIni(profile), 'utf-8');
      logger.info(`Konsole: Updated profile ${defaultProfileName} to ${targetScheme}`);
    } catch (e) {
      logger.error(`Konsole: Failed to update profile: ${e}`);
    }
  }
}
