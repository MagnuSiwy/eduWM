# Modifier masks (X11 values)
SHIFT = "Shift"
SUPER = "Mod4"
CTRL = "Control"
ALT = "Mod1"

MOD = ALT

# Key bindings: [modifier, keysym, callback]
keybinds = [
    [MOD, 't', 'xterm'],
    [MOD, 'f', 'firefox'],
    [MOD, 'k', 'CONFIG_APP'],
    [MOD, 'Left', 'PREVIOUS_WINDOW'],
    [MOD, 'Right', 'NEXT_WINDOW'],
    [MOD, 'c', 'CLOSE'],
    [MOD, 'r', 'RELOAD'],
    [MOD, 'q', 'EXIT'],
    [MOD, '1', 1],
    [MOD, '2', 2],
    [MOD, '3', 3],
    [MOD, '4', 4],
    [MOD, '5', 5],
]

open_welcome_app_on_start = True

# Margins around the group of windows and between the windows
margin_out = 10
margin_in = 5

border_size = 2
# Border color for active and inactive window
# Set to hex colors
border_color_active = "ff0000"
border_color = "222222"

# columns - Divides the screen into columns
# rows - Divides the screen into rows
layout = 'rows'

# wallpaper: [path, mode]
# wallpaper path - full path to the wallpaper
# wallpaper modes:
#   scale - Scale the image to fit the screen and preseve the aspect ratio
#   fill - Scale the image and crop to fit the screen aspect ratio
#   center - Center the image without scaling
wallpaper = ['/home/shrek/eduWM/forest_LeonardoAI.jpg', 'scale']
