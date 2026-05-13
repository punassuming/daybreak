import * as fs from 'fs';
import * as path from 'path';

export function loadJsoncFile(filePath: string): any {
  const raw = fs.readFileSync(filePath, 'utf-8');
  return parseJsonc(raw);
}

export function dumpJsonFile(filePath: string, data: any): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 4) + '\n', 'utf-8');
}

export function parseJsonc(text: string): any {
  const stripped = removeTrailingCommas(stripComments(text));
  return JSON.parse(stripped);
}

function stripComments(text: string): string {
  const result: string[] = [];
  let inString = false;
  let inLineComment = false;
  let inBlockComment = false;
  let escaped = false;
  let i = 0;
  const length = text.length;

  while (i < length) {
    const ch = text[i];
    const nxt = i + 1 < length ? text[i + 1] : '';

    if (inLineComment) {
      if (ch === '\n') { inLineComment = false; result.push(ch); }
      i++;
      continue;
    }
    if (inBlockComment) {
      if (ch === '*' && nxt === '/') { inBlockComment = false; i += 2; continue; }
      if (ch === '\n') result.push(ch);
      i++;
      continue;
    }
    if (inString) {
      result.push(ch);
      if (escaped) {
        escaped = false;
      } else if (ch === '\\') {
        escaped = true;
      } else if (ch === '"') {
        inString = false;
      }
      i++;
      continue;
    }
    if (ch === '/' && nxt === '/') { inLineComment = true; i += 2; continue; }
    if (ch === '/' && nxt === '*') { inBlockComment = true; i += 2; continue; }
    if (ch === '"') inString = true;
    result.push(ch);
    i++;
  }

  return result.join('');
}

function removeTrailingCommas(text: string): string {
  const pattern = /,(\s*[}\]])/g;
  let prev: string | null = null;
  let current = text;
  while (prev !== current) {
    prev = current;
    current = current.replace(pattern, '$1');
  }
  return current;
}
