import curses
from daybreak.themes import THEME_LIBRARY, get_theme_palette
from daybreak.terminals.universal import UniversalPty
from daybreak.config import config

def run_interactive_selector():
    curses.wrapper(_interactive_loop)

def _draw_color_blocks(stdscr, y, x, theme_palette):
    """Draws 16 color blocks"""
    colors = theme_palette.get("colors", {})
    
    stdscr.addstr(y, x, "Palette Preview:", curses.A_BOLD)
    
    # Row 1: Colors 0-7
    for i in range(8):
        try:
            curses.init_pair(10+i, 0, i)
            stdscr.addstr(y+2, x + (i*4), "   ", curses.color_pair(10+i))
            stdscr.addstr(y+3, x + (i*4), f" {i} ", curses.A_NORMAL)
        except:
            pass
            
    # Row 2: Colors 8-15
    for i in range(8, 16):
        try:
            curses.init_pair(10+i, 0, i)
            stdscr.addstr(y+5, x + ((i-8)*4), "   ", curses.color_pair(10+i))
            stdscr.addstr(y+6, x + ((i-8)*4), f" {i} ", curses.A_NORMAL)
        except:
            pass

def _draw_code_mock(stdscr, y, x):
    """Draws a fake code snippet to test contrast"""
    stdscr.addstr(y, x, "Code Syntax Mock:", curses.A_BOLD)
    
    try:
        curses.init_pair(50, 4, -1) # Blue on Default
        curses.init_pair(51, 3, -1) # Yellow on Default
        curses.init_pair(52, 2, -1) # Green on Default
        curses.init_pair(53, 8, -1) # Gray on Default
        curses.init_pair(54, 1, -1) # Red on Default
        curses.init_pair(55, 5, -1) # Magenta on Default
        
        # Let's just draw lines directly for better control
        stdscr.addstr(y+2, x, "def ", curses.color_pair(51))
        stdscr.addstr(y+2, x+4, "calculate_sum", curses.color_pair(50))
        stdscr.addstr(y+2, x+17, "(data):", curses.A_NORMAL)
        
        stdscr.addstr(y+3, x+4, "# This is a comment", curses.color_pair(53))
        
        stdscr.addstr(y+4, x+4, "if ", curses.color_pair(51))
        stdscr.addstr(y+4, x+7, "not ", curses.color_pair(51))
        stdscr.addstr(y+4, x+11, "data: ", curses.A_NORMAL)
        
        stdscr.addstr(y+5, x+8, "return ", curses.color_pair(51))
        stdscr.addstr(y+5, x+15, '"Error"', curses.color_pair(52))
        
    except:
        pass

def _draw_extra_mocks(stdscr, y, x):
    """Draws Diff, Search, and Status Bar mocks"""
    
    # 1. Diff View (Green added, Red removed)
    stdscr.addstr(y, x, "Git Diff Mock:", curses.A_BOLD)
    
    try:
        curses.init_pair(60, 2, -1) # Green FG
        curses.init_pair(61, 1, -1) # Red FG
        
        stdscr.addstr(y+2, x, "+ def new_feature():", curses.color_pair(60))
        stdscr.addstr(y+3, x, "+     return True", curses.color_pair(60))
        stdscr.addstr(y+4, x, "- def old_buggy_code():", curses.color_pair(61))
    except:
        pass
        
    # 2. Search Result (Black text on Yellow BG usually, or Reverse Video)
    stdscr.addstr(y, x + 30, "Search Highlight:", curses.A_BOLD)
    try:
        curses.init_pair(70, 0, 3) # Black on Yellow
        stdscr.addstr(y+2, x + 30, "grep 'pattern' file.txt", curses.A_NORMAL)
        stdscr.addstr(y+3, x + 30, "Found: ", curses.A_NORMAL)
        stdscr.addstr(y+3, x + 37, "pattern", curses.color_pair(70))
        stdscr.addstr(y+3, x + 44, " in line 42", curses.A_NORMAL)
    except:
        pass

    # 3. Status Bar (Powerline style - Blue bg with white text)
    stdscr.addstr(y+6, x, "Status Bar:", curses.A_BOLD)
    try:
        # Status Bar: Blue(4) BG, White(15) FG
        # Note: We rely on colors.py logic ensuring 15 is readable on 4.
        curses.init_pair(80, 15, 4) 
        curses.init_pair(81, 15, 8) # Gray BG
        
        status_text = " NORMAL  master  daybreak/interactive.py "
        stdscr.addstr(y+8, x, status_text, curses.color_pair(80))
        stdscr.addstr(y+8, x + len(status_text), " 90% ", curses.color_pair(81))
    except:
        pass

def _interactive_loop(stdscr):
    # Setup
    curses.curs_set(0) # Hide cursor
    curses.start_color()
    curses.use_default_colors()
    
    pty = UniversalPty()
    themes = sorted(list(THEME_LIBRARY.keys()))
    
    # Load current defaults
    saved_light = config.get_mode_theme_name("light")
    saved_dark = config.get_mode_theme_name("dark")
    
    # Initialize preview mode default to dark
    preview_mode = "dark" 
    
    current_idx = 0
    # Start selection on the saved theme for the current preview mode
    start_theme = saved_dark if preview_mode == "dark" else saved_light
    if start_theme in themes:
        current_idx = themes.index(start_theme)
    
    # Init UI colors
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # Selected Row
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Header
        title = " Daybreak Theme Selector "
        mode_indicator = f" PREVIEW: {preview_mode.upper()} "
        instructions = f" UP/DOWN: Nav | TAB: Toggle Mode | SPACE: Set {preview_mode.upper()} Default | ENTER: Save & Exit | q: Quit "
        
        stdscr.addstr(0, 0, title, curses.A_REVERSE | curses.A_BOLD)
        stdscr.addstr(0, width - len(mode_indicator) - 1, mode_indicator, curses.A_REVERSE)
        stdscr.addstr(1, 0, instructions)
        stdscr.hline(2, 0, curses.ACS_HLINE, width)
        
        # Sidebar (List) - Left 30%
        sidebar_width = 30
        stdscr.vline(3, sidebar_width, curses.ACS_VLINE, height-3)
        
        max_items = height - 4
        start_idx = max(0, current_idx - (max_items // 2))
        end_idx = min(len(themes), start_idx + max_items)
        
        for i in range(start_idx, end_idx):
            theme = themes[i]
            y = 3 + (i - start_idx)
            
            # Markers
            markers = []
            if theme == saved_light: markers.append("L")
            if theme == saved_dark:  markers.append("D")
            
            marker_str = "".join(markers).center(3)
            
            display_str = f" {marker_str} {theme:<20} "
            
            attr = curses.A_NORMAL
            if i == current_idx:
                attr = curses.color_pair(1)
            
            # Draw row
            stdscr.addstr(y, 1, display_str, attr)

        # Preview Area - Right 70%
        palette = get_theme_palette(themes[current_idx]).get(preview_mode, {})
        
        if width > sidebar_width + 20:
            _draw_color_blocks(stdscr, 4, sidebar_width + 4, palette)
            
            if height > 20:
                _draw_code_mock(stdscr, 14, sidebar_width + 4)
            
            if height > 30:
                _draw_extra_mocks(stdscr, 22, sidebar_width + 4)
                
        stdscr.refresh()
        
        # Input handling
        key = stdscr.getch()
        
        if key == ord('q'):
            break
        elif key == curses.KEY_UP:
            if current_idx > 0:
                current_idx -= 1
                pty.apply_theme(themes[current_idx], preview_mode)
        elif key == curses.KEY_DOWN:
            if current_idx < len(themes) - 1:
                current_idx += 1
                pty.apply_theme(themes[current_idx], preview_mode)
        elif key == 9: # TAB key
            preview_mode = "light" if preview_mode == "dark" else "dark"
            # Re-apply theme for new mode
            pty.apply_theme(themes[current_idx], preview_mode)
            
        elif key == 32: # SPACE: Set default for current preview mode
            if preview_mode == "dark":
                saved_dark = themes[current_idx]
            else:
                saved_light = themes[current_idx]
                
        elif key == 10 or key == 13: # ENTER: Save & Exit
            _save_selections(saved_light, saved_dark)
            break

def _save_selections(light_theme, dark_theme):
    try:
        config.set_mode_themes(light_theme, dark_theme)
        print(f"Saved: Light='{light_theme}', Dark='{dark_theme}'")
    except Exception as e:
        print(f"Error saving config: {e}")
