from .colors import generate_light_from_dark, generate_dark_from_light

# --- Base Palettes ---

NORD = {
    "dark": {
        "special": {"background": "#2e3440", "foreground": "#d8dee9", "cursor": "#d8dee9"},
        "colors": {
            "0": "#3b4252", "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
            "4": "#81a1c1", "5": "#b48ead", "6": "#88c0d0", "7": "#e5e9f0",
            "8": "#4c566a", "9": "#bf616a", "10": "#a3be8c", "11": "#ebcb8b",
            "12": "#81a1c1", "13": "#b48ead", "14": "#8fbcbb", "15": "#eceff4"
        }
    },
    "light": {
        "special": {"background": "#e5e9f0", "foreground": "#2e3440", "cursor": "#2e3440"},
        "colors": {
            "0": "#d8dee9", "1": "#bf616a", "2": "#a3be8c", "3": "#ebcb8b",
            "4": "#5e81ac", "5": "#b48ead", "6": "#88c0d0", "7": "#3b4252",
            "8": "#4c566a", "9": "#bf616a", "10": "#a3be8c", "11": "#ebcb8b",
            "12": "#5e81ac", "13": "#b48ead", "14": "#8fbcbb", "15": "#2e3440"
        }
    }
}

GRUVBOX = {
    "dark": {
        "special": {"background": "#282828", "foreground": "#ebdbb2", "cursor": "#ebdbb2"},
        "colors": {
            "0": "#282828", "1": "#cc241d", "2": "#98971a", "3": "#d79921",
            "4": "#458588", "5": "#b16286", "6": "#689d6a", "7": "#a89984",
            "8": "#928374", "9": "#fb4934", "10": "#b8bb26", "11": "#fabd2f",
            "12": "#83a598", "13": "#d3869b", "14": "#8ec07c", "15": "#ebdbb2"
        }
    },
    "light": {
        "special": {"background": "#fbf1c7", "foreground": "#3c3836", "cursor": "#3c3836"},
        "colors": {
            "0": "#fbf1c7", "1": "#cc241d", "2": "#98971a", "3": "#d79921",
            "4": "#458588", "5": "#b16286", "6": "#689d6a", "7": "#7c6f64",
            "8": "#928374", "9": "#9d0006", "10": "#79740e", "11": "#b57614",
            "12": "#076678", "13": "#8f3f71", "14": "#427b58", "15": "#3c3836"
        }
    }
}

DRACULA = {
    "dark": {
        "special": {"background": "#282a36", "foreground": "#f8f8f2", "cursor": "#f8f8f2"},
        "colors": {
            "0": "#21222c", "1": "#ff5555", "2": "#50fa7b", "3": "#f1fa8c",
            "4": "#bd93f9", "5": "#ff79c6", "6": "#8be9fd", "7": "#f8f8f2",
            "8": "#6272a4", "9": "#ff6e6e", "10": "#69ff94", "11": "#ffffa5",
            "12": "#d6acff", "13": "#ff92df", "14": "#a4ffff", "15": "#ffffff"
        }
    },
    # Light will be auto-generated
}

SOLARIZED = {
    "dark": {
        "special": {"background": "#002b36", "foreground": "#839496", "cursor": "#839496"},
        "colors": {
            "0": "#073642", "1": "#dc322f", "2": "#859900", "3": "#b58900",
            "4": "#268bd2", "5": "#d33682", "6": "#2aa198", "7": "#eee8d5",
            "8": "#002b36", "9": "#cb4b16", "10": "#586e75", "11": "#657b83",
            "12": "#839496", "13": "#6c71c4", "14": "#93a1a1", "15": "#fdf6e3"
        }
    },
    "light": {
        "special": {"background": "#fdf6e3", "foreground": "#657b83", "cursor": "#657b83"},
        "colors": {
            "0": "#eee8d5", "1": "#dc322f", "2": "#859900", "3": "#b58900",
            "4": "#268bd2", "5": "#d33682", "6": "#2aa198", "7": "#073642",
            "8": "#fdf6e3", "9": "#cb4b16", "10": "#586e75", "11": "#657b83",
            "12": "#839496", "13": "#6c71c4", "14": "#93a1a1", "15": "#002b36"
        }
    }
}

CATPPUCCIN = {
    "dark": { # Mocha
        "special": {"background": "#1e1e2e", "foreground": "#cdd6f4", "cursor": "#cdd6f4"},
        "colors": {
            "0": "#45475a", "1": "#f38ba8", "2": "#a6e3a1", "3": "#f9e2af",
            "4": "#89b4fa", "5": "#f5c2e7", "6": "#94e2d5", "7": "#bac2de",
            "8": "#585b70", "9": "#f38ba8", "10": "#a6e3a1", "11": "#f9e2af",
            "12": "#89b4fa", "13": "#f5c2e7", "14": "#94e2d5", "15": "#a6adc8"
        }
    },
    "light": { # Latte
        "special": {"background": "#eff1f5", "foreground": "#4c4f69", "cursor": "#4c4f69"},
        "colors": {
            "0": "#5c5f77", "1": "#d20f39", "2": "#40a02b", "3": "#df8e1d",
            "4": "#1e66f5", "5": "#ea76cb", "6": "#179299", "7": "#acb0be",
            "8": "#6c6f85", "9": "#d20f39", "10": "#40a02b", "11": "#df8e1d",
            "12": "#1e66f5", "13": "#ea76cb", "14": "#179299", "15": "#bcc0cc"
        }
    }
}

TOKYO_NIGHT = {
    "dark": {
        "special": {"background": "#1a1b26", "foreground": "#c0caf5", "cursor": "#c0caf5"},
        "colors": {
            "0": "#15161e", "1": "#f7768e", "2": "#9ece6a", "3": "#e0af68",
            "4": "#7aa2f7", "5": "#bb9af7", "6": "#7dcfff", "7": "#a9b1d6",
            "8": "#414868", "9": "#f7768e", "10": "#9ece6a", "11": "#e0af68",
            "12": "#7aa2f7", "13": "#bb9af7", "14": "#7dcfff", "15": "#c0caf5"
        }
    },
    "light": {
        "special": {"background": "#e1e2e7", "foreground": "#3760bf", "cursor": "#3760bf"},
        "colors": {
            "0": "#d5d6db", "1": "#f52a65", "2": "#587539", "3": "#8c6c3e",
            "4": "#2e5cb8", "5": "#9854f1", "6": "#007197", "7": "#6172b0",
            "8": "#a1a6b2", "9": "#f52a65", "10": "#587539", "11": "#8c6c3e",
            "12": "#2e5cb8", "13": "#9854f1", "14": "#007197", "15": "#3760bf"
        }
    }
}

MONOKAI = {
    "dark": {
        "special": {"background": "#272822", "foreground": "#f8f8f2", "cursor": "#f8f8f2"},
        "colors": {
            "0": "#272822", "1": "#f92672", "2": "#a6e22e", "3": "#f4bf75",
            "4": "#66d9ef", "5": "#ae81ff", "6": "#a1efe4", "7": "#f8f8f2",
            "8": "#75715e", "9": "#f92672", "10": "#a6e22e", "11": "#f4bf75",
            "12": "#66d9ef", "13": "#ae81ff", "14": "#a1efe4", "15": "#f9f8f5"
        }
    }
}

ONE_DARK = {
    "dark": {
        "special": {"background": "#282c34", "foreground": "#abb2bf", "cursor": "#abb2bf"},
        "colors": {
            "0": "#282c34", "1": "#e06c75", "2": "#98c379", "3": "#e5c07b",
            "4": "#61afef", "5": "#c678dd", "6": "#56b6c2", "7": "#abb2bf",
            "8": "#5c6370", "9": "#e06c75", "10": "#98c379", "11": "#e5c07b",
            "12": "#61afef", "13": "#c678dd", "14": "#56b6c2", "15": "#ffffff"
        }
    }
}

# Master Library
THEME_LIBRARY = {
    "Nord": NORD,
    "Gruvbox": GRUVBOX,
    "Dracula": DRACULA,
    "Solarized": SOLARIZED,
    "Catppuccin": CATPPUCCIN,
    "Tokyo Night": TOKYO_NIGHT,
    "Monokai": MONOKAI,
    "One Dark": ONE_DARK,
}

def get_theme_palette(theme_name):
    """
    Returns a dict with 'light' and 'dark' keys. 
    If one is missing, it is generated.
    """
    base = THEME_LIBRARY.get(theme_name)
    if not base:
        # Fallback
        return NORD
    
    result = base.copy()
    
    if "light" not in result and "dark" in result:
        result["light"] = generate_light_from_dark(result["dark"])
        result["light"]["generated"] = True # Flag logic
        
    if "dark" not in result and "light" in result:
        result["dark"] = generate_dark_from_light(result["light"])
        result["dark"]["generated"] = True

    return result
