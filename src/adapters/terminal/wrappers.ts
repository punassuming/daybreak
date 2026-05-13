import { Terminal } from '../../terminals/base';
import { UniversalPty } from '../../terminals/universal';
import { Palette } from '../../colors';

export class UniversalPtyAdapter {
  name = 'universal_pty';
  private terminal: UniversalPty;

  constructor() {
    this.terminal = new UniversalPty();
  }

  applyMode(mode: string, themeName: string, _palette?: Palette): void {
    this.terminal.applyTheme(themeName, mode);
  }
}

export class LegacyModeTerminalAdapter {
  name: string;
  private terminal: Terminal;

  constructor(terminal: Terminal, name?: string) {
    this.terminal = terminal;
    this.name = name || terminal.constructor.name;
  }

  applyMode(mode: string, _themeName: string, _palette?: Palette): void {
    this.terminal.setMode(mode);
  }
}
