export interface PaletteSpecial {
  background: string;
  foreground: string;
  cursor: string;
}

export interface Palette {
  special: PaletteSpecial;
  colors: Record<string, string>;
  generated?: boolean;
}

export function hexToRgb(hex: string): [number, number, number] {
  const h = hex.replace('#', '');
  return [
    parseInt(h.slice(0, 2), 16),
    parseInt(h.slice(2, 4), 16),
    parseInt(h.slice(4, 6), 16),
  ];
}

export function rgbToHex(rgb: [number, number, number]): string {
  return '#' + rgb.map(v => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, '0')).join('');
}

function rgbToHls(r: number, g: number, b: number): [number, number, number] {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  // Return in HLS order (h, l, s) to match Python colorsys
  return [h, l, s];
}

function hlsToRgb(h: number, l: number, s: number): [number, number, number] {
  if (s === 0) {
    const v = Math.round(l * 255);
    return [v, v, v];
  }
  const hue2rgb = (p: number, q: number, t: number): number => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };
  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;
  return [
    Math.round(hue2rgb(p, q, h + 1 / 3) * 255),
    Math.round(hue2rgb(p, q, h) * 255),
    Math.round(hue2rgb(p, q, h - 1 / 3) * 255),
  ];
}

export function getLuminance(r: number, g: number, b: number): number {
  const a = [r, g, b].map(x => {
    const v = x / 255.0;
    return v > 0.03928 ? Math.pow((v + 0.055) / 1.055, 2.4) : v / 12.92;
  });
  return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
}

export function getContrastRatio(hex1: string, hex2: string): number {
  const [r1, g1, b1] = hexToRgb(hex1);
  const [r2, g2, b2] = hexToRgb(hex2);
  const l1 = getLuminance(r1, g1, b1);
  const l2 = getLuminance(r2, g2, b2);
  if (l1 > l2) return (l1 + 0.05) / (l2 + 0.05);
  return (l2 + 0.05) / (l1 + 0.05);
}

export function adjustColorForContrast(fgHex: string, bgHex: string, minRatio = 4.5): string {
  const currentRatio = getContrastRatio(fgHex, bgHex);
  if (currentRatio >= minRatio) return fgHex;

  const [r, g, b] = hexToRgb(fgHex);
  let [h, l, s] = rgbToHls(r, g, b);

  const [bgR, bgG, bgB] = hexToRgb(bgHex);
  const bgLum = getLuminance(bgR, bgG, bgB);

  const direction = bgLum < 0.5 ? 1 : -1;
  const step = 0.05;
  const maxSteps = 20;

  let bestHex = fgHex;
  let bestRatio = currentRatio;

  for (let i = 0; i < maxSteps; i++) {
    l = Math.max(0.0, Math.min(1.0, l + step * direction));
    const newRgb = hlsToRgb(h, l, s);
    const newHex = rgbToHex([
      Math.max(0, Math.min(255, newRgb[0])),
      Math.max(0, Math.min(255, newRgb[1])),
      Math.max(0, Math.min(255, newRgb[2])),
    ]);
    const newRatio = getContrastRatio(newHex, bgHex);
    if (newRatio > bestRatio) {
      bestRatio = newRatio;
      bestHex = newHex;
    }
    if (newRatio >= minRatio) return newHex;
  }
  return bestHex;
}

export function invertLightness(hexColor: string, targetL?: number): string {
  const [r, g, b] = hexToRgb(hexColor);
  const [h, l, s] = rgbToHls(r, g, b);
  const newL = targetL !== undefined ? targetL : 1.0 - l;
  const newRgb = hlsToRgb(h, newL, s);
  return rgbToHex([
    Math.max(0, Math.min(255, newRgb[0])),
    Math.max(0, Math.min(255, newRgb[1])),
    Math.max(0, Math.min(255, newRgb[2])),
  ]);
}

export function generateLightFromDark(darkPalette: Palette): Palette {
  const light: Palette = { special: { background: '', foreground: '', cursor: '' }, colors: {} };

  const bgOrig = darkPalette.special.background;
  light.special.background = invertLightness(bgOrig, 0.96);
  const bgHex = light.special.background;

  const fgOrig = darkPalette.special.foreground;
  const fgCandidate = invertLightness(fgOrig, 0.15);
  light.special.foreground = adjustColorForContrast(fgCandidate, bgHex, 7.0);
  light.special.cursor = light.special.foreground;

  const colorsToAdjust = { ...darkPalette.colors };

  for (const [i, color] of Object.entries(colorsToAdjust)) {
    const [r, g, b] = hexToRgb(color);
    let [h, l, s] = rgbToHls(r, g, b);

    let newL = Math.max(0.2, Math.min(0.45, l * 0.5));
    let newS = Math.min(1.0, s * 1.1);

    if (i === '3' || i === '11') {
      newL = Math.max(0.2, Math.min(0.35, l * 0.4));
      newS = Math.min(1.0, s * 1.3);
      if (h > 0.14 && h < 0.18) h = 0.10;
    }

    const rawRgb = hlsToRgb(h, newL, newS);
    const rawHex = rgbToHex([rawRgb[0], rawRgb[1], rawRgb[2]]);
    light.colors[i] = adjustColorForContrast(rawHex, bgHex, 4.0);
  }

  // Post-adjustments
  light.colors['0'] = adjustColorForContrast(light.colors['0'] || '#000000', light.colors['3'] || '#ffffff', 4.5);
  light.colors['15'] = '#ffffff';

  return light;
}

export function generateDarkFromLight(lightPalette: Palette): Palette {
  const dark: Palette = { special: { background: '', foreground: '', cursor: '' }, colors: {} };

  const bgOrig = lightPalette.special.background;
  dark.special.background = invertLightness(bgOrig, 0.10);
  const bgHex = dark.special.background;

  const fgOrig = lightPalette.special.foreground;
  const fgCandidate = invertLightness(fgOrig, 0.85);
  dark.special.foreground = adjustColorForContrast(fgCandidate, bgHex, 7.0);
  dark.special.cursor = dark.special.foreground;

  for (const [i, color] of Object.entries(lightPalette.colors)) {
    const [r, g, b] = hexToRgb(color);
    const [h, l, s] = rgbToHls(r, g, b);
    const newL = Math.min(0.85, Math.max(0.6, l * 2.0));
    const rawRgb = hlsToRgb(h, newL, s);
    const rawHex = rgbToHex([rawRgb[0], rawRgb[1], rawRgb[2]]);
    dark.colors[i] = adjustColorForContrast(rawHex, bgHex, 4.0);
  }

  return dark;
}
