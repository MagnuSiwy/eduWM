# Modifier masks (X11 values)
SHIFT = "Shift"
SUPER = "Mod4"
CTRL = "Control"
ALT = "Mod1"

MOD = ALT

# Key bindings: (keysym, modifiers, callback)
keybinds = [
    (MOD, "t", "xterm"),
    (MOD, "f", "firefox"),
    (MOD, "Left", "PREVIOUS_WINDOW"),
    (MOD, "Right", "NEXT_WINDOW"),
    (MOD, "c", "CLOSE"),
    (MOD, "q", "EXIT"),
]