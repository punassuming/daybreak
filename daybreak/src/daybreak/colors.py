import colorsys

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def invert_lightness(hex_color, target_l=None):
    """
    Inverts the lightness of a color in HLS space.
    If target_l is provided, snaps the lightness to that approximate value relative to 0-1.
    """
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    if target_l is not None:
        new_l = target_l
    else:
        new_l = 1.0 - l
        
    r, g, b = colorsys.hls_to_rgb(h, new_l, s)
    return rgb_to_hex((max(0, min(255, r*255)), max(0, min(255, g*255)), max(0, min(255, b*255))))

def generate_light_from_dark(dark_palette):
    """
    Algorithmic generation of a light palette from a dark one.
    Strategy:
    1. Swap BG and FG, inverting their lightness.
    2. Darken the ANSI colors so they are readable on light BG.
    """
    light = {"special": {}, "colors": {}}
    
    # 1. Special Colors (BG/FG)
    # Background: Dark -> Light (High L)
    light['special']['background'] = invert_lightness(dark_palette['special']['background'], target_l=0.93) # Off-white
    # Foreground: Light -> Dark (Low L)
    light['special']['foreground'] = invert_lightness(dark_palette['special']['foreground'], target_l=0.2) # Dark grey
    light['special']['cursor'] = light['special']['foreground']

    # 2. ANSI Colors
    # For a light theme, we generally want darker/more saturated versions of the pastel dark-theme colors
    # so they have contrast against white.
    for i, color in dark_palette['colors'].items():
        # Reduce lightness to make it darker
        # But don't just invert, scaling is better.
        r, g, b = hex_to_rgb(color)
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        
        # Heuristic: Map lightness from [0.5, 0.9] to [0.3, 0.5]
        new_l = max(0.2, l * 0.6) 
        
        r, g, b = colorsys.hls_to_rgb(h, new_l, s)
        light['colors'][i] = rgb_to_hex((r*255, g*255, b*255))
        
    return light

def generate_dark_from_light(light_palette):
    """
    Algorithmic generation of a dark palette from a light one.
    """
    dark = {"special": {}, "colors": {}}
    
    dark['special']['background'] = invert_lightness(light_palette['special']['background'], target_l=0.10)
    dark['special']['foreground'] = invert_lightness(light_palette['special']['foreground'], target_l=0.85)
    dark['special']['cursor'] = dark['special']['foreground']

    for i, color in light_palette['colors'].items():
        r, g, b = hex_to_rgb(color)
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        
        # Lighten colors for dark background
        new_l = min(0.9, l * 1.5)
        
        r, g, b = colorsys.hls_to_rgb(h, new_l, s)
        dark['colors'][i] = rgb_to_hex((r*255, g*255, b*255))
        
    return dark
