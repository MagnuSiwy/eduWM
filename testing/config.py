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
]

# mouse - Always move mouse to the focused window

focus = "mouse"

# wallpaper: [path, mode]
# wallpaper path - path to your wallpaper
# wallpaper modes:
#   scale - Scale the image to fit the screen and preseve the aspect ratio
#   fill - Scale the image and crop to fit the screen aspect ratio
#   center - Center the image without scaling
wallpaper = ["~/eduWM/forest_LeonardoAI.jpg", "scale"]