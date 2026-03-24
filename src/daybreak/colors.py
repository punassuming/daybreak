import colorsys
import math

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def get_luminance(r, g, b):
    # sRGB luminance calculation
    a = [x / 255.0 for x in (r, g, b)]
    a = [((x + 0.055) / 1.055) ** 2.4 if x > 0.03928 else x / 12.92 for x in a]
    return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]

def get_contrast_ratio(hex1, hex2):
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    
    l1 = get_luminance(r1, g1, b1)
    l2 = get_luminance(r2, g2, b2)
    
    if l1 > l2:
        return (l1 + 0.05) / (l2 + 0.05)
    else:
        return (l2 + 0.05) / (l1 + 0.05)

def adjust_color_for_contrast(fg_hex, bg_hex, min_ratio=4.5):
    """
    Adjusts fg_hex lightness to ensure it meets min_ratio against bg_hex.
    """
    current_ratio = get_contrast_ratio(fg_hex, bg_hex)
    if current_ratio >= min_ratio:
        return fg_hex
        
    r, g, b = hex_to_rgb(fg_hex)
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    bg_r, bg_g, bg_b = hex_to_rgb(bg_hex)
    bg_l = get_luminance(bg_r, bg_g, bg_b)
    
    # Decide direction: darken or lighten?
    # If BG is dark (lum < 0.5), we usually want to lighten FG.
    # If BG is light, we darken FG.
    
    # However, sometimes we might have a light FG on a light BG, so we need to darken.
    # We try moving L towards 0 or 1.
    
    step = 0.05
    max_steps = 20
    
    # Determine target direction based on BG luminance
    if bg_l < 0.5:
        # Dark background -> Lighten text
        direction = 1
    else:
        # Light background -> Darken text
        direction = -1
        
    # Heuristic: If we are already logically "wrong" (e.g. dark text on dark bg), 
    # we might need to flip significantly.
    
    best_hex = fg_hex
    best_ratio = current_ratio
    
    for _ in range(max_steps):
        l = max(0.0, min(1.0, l + (step * direction)))
        new_rgb = colorsys.hls_to_rgb(h, l, s)
        new_hex = rgb_to_hex((max(0, min(255, new_rgb[0]*255)), 
                              max(0, min(255, new_rgb[1]*255)), 
                              max(0, min(255, new_rgb[2]*255))))
        
        new_ratio = get_contrast_ratio(new_hex, bg_hex)
        
        if new_ratio > best_ratio:
            best_ratio = new_ratio
            best_hex = new_hex
            
        if new_ratio >= min_ratio:
            return new_hex
            
    return best_hex

def invert_lightness(hex_color, target_l=None):
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    if target_l is not None:
        new_l = target_l
    else:
        new_l = 1.0 - l
        
    r, g, b = colorsys.hls_to_rgb(h, new_l, s)
    return rgb_to_hex((max(0, min(255, r*255)), max(0, min(255, g*255)), max(0, min(255, b*255))))

def generate_light_from_dark(dark_palette):
    light = {"special": {}, "colors": {}}
    
    # 1. Background (Dark -> Light)
    # Ensure it's very light for good contrast
    bg_orig = dark_palette['special']['background']
    light['special']['background'] = invert_lightness(bg_orig, target_l=0.96)
    bg_hex = light['special']['background']

    # 2. Foreground (Light -> Dark)
    fg_orig = dark_palette['special']['foreground']
    # Start with a simple inversion/darkening
    fg_candidate = invert_lightness(fg_orig, target_l=0.15)
    # Enforce strong contrast (7:1 for main text is ideal for readability)
    light['special']['foreground'] = adjust_color_for_contrast(fg_candidate, bg_hex, min_ratio=7.0)
    light['special']['cursor'] = light['special']['foreground']

    # 3. ANSI Colors
    # Critical UI Pairs to Check:
    # - Search: Yellow(3) BG vs Black(0) FG  (or vice versa)
    # - Status: Blue(4) BG vs White(15) FG
    # - Keywords: Yellow(3), Red(1), Green(2) vs Main BG
    
    colors_to_adjust = dark_palette['colors'].copy()
    
    for i, color in colors_to_adjust.items():
        # Heuristic: Map lightness to darker range
        r, g, b = hex_to_rgb(color)
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        
        # Darken significantly: 0.8 -> 0.35 roughly
        new_l = max(0.2, min(0.45, l * 0.5))
        
        # Boost saturation slightly
        new_s = min(1.0, s * 1.1)
        
        # Special handling for Yellow (3/11) in Light Mode -> Needs to be Orange/Brown for visibility
        if i in ['3', '11']:
            new_l = max(0.2, min(0.35, l * 0.4)) # Make it darker
            new_s = min(1.0, s * 1.3) # More saturated
            # Shift hue slightly towards orange if it's too lemon-yellow
            if 0.14 < h < 0.18: # Yellow range
                h = 0.10 # Orange
        
        raw_rgb = colorsys.hls_to_rgb(h, new_l, new_s)
        raw_hex = rgb_to_hex((raw_rgb[0]*255, raw_rgb[1]*255, raw_rgb[2]*255))
        
        # Enforce contrast against Main Background
        adjusted_hex = adjust_color_for_contrast(raw_hex, bg_hex, min_ratio=4.0)
        light['colors'][i] = adjusted_hex

    # Post-Adjustment Validation for UI Elements
    
    # 1. Search Highlight (Yellow(3) BG vs Black(0) FG)
    # Ensure Black(0) is dark enough
    light['colors']['0'] = adjust_color_for_contrast(light['colors']['0'], light['colors']['3'], min_ratio=4.5)
    
    # 2. Status Bar (Blue(4) BG vs White(15) FG)
    # Ensure White(15) contrasts with Blue(4)
    # Since Blue(4) is now dark (for text visibility on white BG), it might be TOO dark?
    # Actually, for light mode, Blue(4) is usually dark blue.
    # So White(15) (which is usually dark gray in light mode context if inverted blindly) needs check.
    
    # Wait, in Light Mode, ANSI 15 is usually White (Background-ish) or Black (Foreground-ish)?
    # Standard: 0=Black, 7=Gray, 15=White.
    # BUT in a "Light Theme", Foreground is Dark.
    # Usually: 0=DarkGray, 7=LightGray, 15=White (Background).
    
    # Let's force ANSI 15 to be truly Light/White for status bar usage
    # But wait, if 15 is White, and 0 is Dark...
    # The previous logic might have darkened 15 too much.
    
    # Let's ensure 15 is LIGHT (White) in Light Mode, not Dark.
    # Why? Because 0 is usually the Main Text (Dark). 15 is usually Bright White.
    # If we mapped 15 to Dark, status bars (Blue BG + Dark Text) would be low contrast if Blue is Dark.
    
    # Correction: In Light Themes, ANSI Colors (1-6) are Dark.
    # ANSI 0 is usually Light Gray (or Black?).
    # ANSI 7 is usually Dark Gray.
    # ANSI 15 is usually White (Background).
    
    # Let's explicitly set 15 to White/High-Luminance for Light Mode
    light['colors']['15'] = "#ffffff" 
    
    # Now check Blue(4) against White(15)
    # Blue(4) was darkened to read on White BG. So Blue(4) is Dark Blue.
    # Dark Blue vs White -> Good Contrast.
    
    return light

def generate_dark_from_light(light_palette):
    dark = {"special": {}, "colors": {}}
    
    # 1. Background
    bg_orig = light_palette['special']['background']
    dark['special']['background'] = invert_lightness(bg_orig, target_l=0.10) # Dark gray/black
    bg_hex = dark['special']['background']

    # 2. Foreground
    fg_orig = light_palette['special']['foreground']
    fg_candidate = invert_lightness(fg_orig, target_l=0.85)
    dark['special']['foreground'] = adjust_color_for_contrast(fg_candidate, bg_hex, min_ratio=7.0)
    dark['special']['cursor'] = dark['special']['foreground']

    # 3. ANSI Colors
    for i, color in light_palette['colors'].items():
        r, g, b = hex_to_rgb(color)
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        
        # Lighten: 0.3 -> 0.7 roughly
        new_l = min(0.85, max(0.6, l * 2.0))
        
        raw_rgb = colorsys.hls_to_rgb(h, new_l, s)
        raw_hex = rgb_to_hex((raw_rgb[0]*255, raw_rgb[1]*255, raw_rgb[2]*255))
        
        dark['colors'][i] = adjust_color_for_contrast(raw_hex, bg_hex, min_ratio=4.0)
        
    return dark