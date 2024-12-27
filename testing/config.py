# Modifier masks (X11 values)
SHIFT = "Shift"
SUPER = "Mod4"
CTRL = "Control"
ALT = "Mod1"

MOD = ALT

# Key bindings: [keysym, modifiers, callback]
keybinds = [
    [MOD, "t", "xterm"],
    [MOD, "f", "firefox"],
    [MOD, "Left", "PREVIOUS_WINDOW"],
    [MOD, "Right", "NEXT_WINDOW"],
    [MOD, "c", "CLOSE"],
    [MOD, "r", "RELOAD"],
    [MOD, "q", "EXIT"],
    [MOD, "1", 1],
    [MOD, "2", 2],
    [MOD, "3", 3],
    [MOD, "4", 4],
    [MOD, "5", 5],
]

# mouse - Always move mouse to the focused window

focus = "mouse"

margin_out = 10
margin_in = 5
border_size = 2

layout = "column"

# wallpaper: [path, mode]
# wallpaper path - full path to your wallpaper
# wallpaper modes:
#   scale - Scale the image to fit the screen and preseve the aspect ratio
#   fill - Scale the image and crop to fit the screen aspect ratio
#   center - Center the image without scaling
wallpaper = ["/home/shrek/eduWM/forest_LeonardoAI.jpg", "scale"]