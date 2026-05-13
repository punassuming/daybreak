import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import { parse as parseToml } from 'smol-toml';

const logger = {
  info: (m: string) => {},
  warn: (m: string) => console.warn('[daybreak]', m),
  error: (m: string) => console.error('[daybreak]', m),
  debug: (m: string) => {},
};

export const CURRENT_SCHEMA_VERSION = 2;

export interface DaybreakConfig {
  schema_version: number;
  system: {
    linux_kde_light: string;
    linux_kde_dark: string;
    windows_light_reg: number;
    windows_dark_reg: number;
  };
  theme: {
    active: string;
    light: string;
    dark: string;
  };
  integrations: {
    windows_terminal_light_scheme: string;
    windows_terminal_dark_scheme: string;
    obsidian_light_theme: string;
    obsidian_dark_theme: string;
    neovim_light_scheme: string;
    neovim_dark_scheme: string;
  };
  [key: string]: any;
}

export const DEFAULT_CONFIG: DaybreakConfig = {
  schema_version: CURRENT_SCHEMA_VERSION,
  system: {
    linux_kde_light: 'BreathLight',
    linux_kde_dark: 'BreathDark',
    windows_light_reg: 1,
    windows_dark_reg: 0,
  },
  theme: {
    active: 'Nord',
    light: 'Nord',
    dark: 'Nord',
  },
  integrations: {
    windows_terminal_light_scheme: 'One Half Light',
    windows_terminal_dark_scheme: 'One Half Dark',
    obsidian_light_theme: 'moonstone',
    obsidian_dark_theme: 'obsidian',
    neovim_light_scheme: 'tokyonight-day',
    neovim_dark_scheme: 'tokyonight',
  },
};

export class ConfigManager {
  configDir: string;
  configFile: string;
  data: DaybreakConfig;

  constructor(configDir?: string) {
    const envConfigDir = process.env['DAYBREAK_CONFIG_DIR'];
    if (configDir != null) {
      this.configDir = configDir;
    } else if (envConfigDir) {
      this.configDir = envConfigDir;
    } else {
      this.configDir = path.join(os.homedir(), '.config', 'daybreak');
    }
    this.configFile = path.join(this.configDir, 'config.toml');
    this.data = this._load();
  }

  private _load(): DaybreakConfig {
    if (!fs.existsSync(this.configFile)) {
      return this._createDefault();
    }
    let rawData: any;
    try {
      const text = fs.readFileSync(this.configFile, 'utf-8');
      rawData = parseToml(text);
    } catch (exc) {
      logger.error(`Failed to load config: ${exc}. Using defaults.`);
      return structuredClone(DEFAULT_CONFIG);
    }
    const { migrated, changed } = this._migrate(rawData);
    if (changed) {
      try {
        this._save(migrated);
      } catch (exc) {
        logger.warn(`Failed to write migrated config: ${exc}`);
      }
    }
    return migrated;
  }

  private _createDefault(): DaybreakConfig {
    const data = structuredClone(DEFAULT_CONFIG);
    try {
      this._save(data);
    } catch (exc) {
      logger.warn(`Failed to persist default config: ${exc}`);
    }
    return data;
  }

  private _save(data: DaybreakConfig): void {
    fs.mkdirSync(this.configDir, { recursive: true });
    fs.writeFileSync(this.configFile, toToml(data), 'utf-8');
  }

  private _migrate(rawData: any): { migrated: DaybreakConfig; changed: boolean } {
    if (!rawData || typeof rawData !== 'object') {
      return { migrated: structuredClone(DEFAULT_CONFIG), changed: true };
    }
    const migrated: any = structuredClone(rawData);
    let changed = false;

    if (migrated.schema_version !== CURRENT_SCHEMA_VERSION) {
      migrated.schema_version = CURRENT_SCHEMA_VERSION;
      changed = true;
    }

    let systemCfg = migrated.system;
    if (!systemCfg || typeof systemCfg !== 'object') {
      systemCfg = {};
      changed = true;
    }
    for (const [key, defaultValue] of Object.entries(DEFAULT_CONFIG.system) as [string, any][]) {
      if (!(key in systemCfg)) {
        systemCfg[key] = defaultValue;
        changed = true;
      }
    }
    migrated.system = systemCfg;

    const legacyTerminal = (migrated.terminal && typeof migrated.terminal === 'object') ? migrated.terminal : {};
    let themeCfg = migrated.theme;
    if (!themeCfg || typeof themeCfg !== 'object') {
      themeCfg = {};
      changed = true;
    }

    const active = themeCfg.active || legacyTerminal.theme || DEFAULT_CONFIG.theme.active;
    const light = themeCfg.light || legacyTerminal.theme_light || active;
    const dark = themeCfg.dark || legacyTerminal.theme_dark || active;
    const normalizedTheme = { active, light, dark };

    if (JSON.stringify(themeCfg) !== JSON.stringify(normalizedTheme)) changed = true;
    migrated.theme = normalizedTheme;

    let integrationsCfg = migrated.integrations;
    if (!integrationsCfg || typeof integrationsCfg !== 'object') {
      integrationsCfg = {};
      changed = true;
    }
    for (const [key, defaultValue] of Object.entries(DEFAULT_CONFIG.integrations) as [string, any][]) {
      if (!(key in integrationsCfg)) {
        integrationsCfg[key] = defaultValue;
        changed = true;
      }
    }
    migrated.integrations = integrationsCfg;

    if ('terminal' in migrated) {
      delete migrated.terminal;
      changed = true;
    }

    return { migrated: migrated as DaybreakConfig, changed };
  }

  save(): void {
    try {
      this._save(this.data);
    } catch (exc) {
      logger.warn(`Failed to save config: ${exc}`);
    }
  }

  reload(): void {
    try {
      this.data = this._load();
    } catch (exc) {
      logger.warn(`Failed to reload config: ${exc}`);
    }
  }

  get(section: string, key: string, defaultValue?: any): any {
    const sectionData = this.data[section];
    if (!sectionData || typeof sectionData !== 'object') return defaultValue;
    return (key in sectionData) ? sectionData[key] : defaultValue;
  }

  getSystemTheme(osType: string, mode: string): string | null {
    if (osType === 'linux_kde') {
      const key = mode === 'light' ? 'linux_kde_light' : 'linux_kde_dark';
      return this.get('system', key, (DEFAULT_CONFIG.system as any)[key]);
    }
    return null;
  }

  getActiveThemeName(): string {
    return this.get('theme', 'active', DEFAULT_CONFIG.theme.active);
  }

  getModeThemeName(mode: string): string {
    if (mode === 'light') return this.get('theme', 'light', this.getActiveThemeName());
    if (mode === 'dark') return this.get('theme', 'dark', this.getActiveThemeName());
    return this.getActiveThemeName();
  }

  getTerminalThemeName(mode?: string): string {
    if (mode === 'light' || mode === 'dark') return this.getModeThemeName(mode);
    return this.getActiveThemeName();
  }

  setModeThemes(lightTheme: string, darkTheme: string): void {
    if (!this.data.theme) this.data.theme = { active: darkTheme, light: lightTheme, dark: darkTheme };
    this.data.theme.light = lightTheme;
    this.data.theme.dark = darkTheme;
    if (!this.data.theme.active) this.data.theme.active = darkTheme;
    this.save();
  }
}

export function toToml(data: Record<string, any>): string {
  const lines: string[] = [];
  appendTable(lines, data, null);
  return lines.join('\n').trim() + '\n';
}

function appendTable(lines: string[], table: Record<string, any>, prefix: string | null): void {
  const scalarItems: [string, any][] = [];
  const nestedItems: [string, Record<string, any>][] = [];

  for (const [key, value] of Object.entries(table)) {
    if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
      nestedItems.push([key, value]);
    } else {
      scalarItems.push([key, value]);
    }
  }

  if (prefix) {
    lines.push(`[${prefix}]`);
  }
  for (const [key, value] of scalarItems) {
    lines.push(`${key} = ${formatTomlValue(value)}`);
  }

  if (scalarItems.length > 0 && nestedItems.length > 0) {
    lines.push('');
  }

  for (let i = 0; i < nestedItems.length; i++) {
    const [key, nested] = nestedItems[i];
    const childPrefix = prefix ? `${prefix}.${key}` : key;
    appendTable(lines, nested, childPrefix);
    if (i !== nestedItems.length - 1) {
      lines.push('');
    }
  }
}

export function formatTomlValue(value: any): string {
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'number') return String(value);
  const escaped = String(value).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
  return `"${escaped}"`;
}

export let config = new ConfigManager();

export function resetConfig(c: ConfigManager): void {
  config = c;
}
