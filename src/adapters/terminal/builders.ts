import { Ghostty, WezTerm } from '../../terminals/configTerminals';
import { Kitty } from '../../terminals/kitty';
import { Konsole } from '../../terminals/konsole';
import { Neovim } from '../../terminals/neovim';
import { WindowsTerminalAdapter } from './windowsTerminal';
import { LegacyModeTerminalAdapter, UniversalPtyAdapter } from './wrappers';

export function buildLinuxTerminalAdapters() {
  return [
    new UniversalPtyAdapter(),
    new LegacyModeTerminalAdapter(new Neovim()),
    new LegacyModeTerminalAdapter(new Kitty()),
    new LegacyModeTerminalAdapter(new Ghostty()),
    new LegacyModeTerminalAdapter(new WezTerm()),
    new LegacyModeTerminalAdapter(new Konsole()),
  ];
}

export function buildWindowsTerminalAdapters() {
  return [
    new WindowsTerminalAdapter(),
  ];
}
