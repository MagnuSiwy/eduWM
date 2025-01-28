import gi
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wm import config

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk

class ConfigApp():
    def __init__(self):
        self.builder = Gtk.Builder()
        self.gladeFile = os.path.join(os.path.dirname(__file__), "eduWMconfig.glade")
        self.configFile = os.path.join(os.path.dirname(__file__), "../wm/config.py")
        self.builder.add_from_file(self.gladeFile)
        self.builder.connect_signals(self)
        self.selected = None
        self.selectedRow = None
        self.keybindsChanges = []
        self.windowChanges = []
        self.othersChanges = []
        self.lastEntryText = None
        self.entryBuffers = { "margin_out": None, "margin_in": None, "layout": None, "border_size": None, "wallpaperPath": None, "wallpaperMode": None }
        
        self.welcomeCheckbox = self.builder.get_object("welcomeCheckbox")
        self.keybindsTreeView = self.builder.get_object("keybindsTreeView")
        self.keybindsListstore = self.builder.get_object("keybindsListstore")

        self.loadModel(self.keybindsListstore, config.keybinds)
        for key in self.entryBuffers.keys():
            if key.startswith("wallpaper"):
                continue
            self.loadBuffer(key)
        self.loadWallpaperBuffers()
        self.checkboxInit()

        window = self.builder.get_object("mainWindow")
        window.set_deletable(False)
        window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        window.show()

    def onQuit(widget, arg):
        Gtk.main_quit()
        return True

    def loadModel(self, liststore, data):
        for row in data:
            liststore.append([row[1],str(row[2])])

    def loadBuffer(self, key):
        buffer = self.builder.get_object(f"{key}Buffer")
        text = str(getattr(config, key))
        self.entryBuffers[key] = buffer
        buffer.set_text(text, len(text))

    def loadWallpaperBuffers(self):
        pathBuffer = self.builder.get_object("wallpaperPathBuffer")
        appBuffer = self.builder.get_object("wallpaperModeBuffer")
        wallpaperAttribute = getattr(config, "wallpaper")
        self.entryBuffers["wallpaperPath"] = pathBuffer
        self.entryBuffers["wallpaperMode"] = appBuffer
        pathBuffer.set_text(wallpaperAttribute[0], len(wallpaperAttribute[0]))
        appBuffer.set_text(wallpaperAttribute[1], len(wallpaperAttribute[1]))

    def checkboxInit(self):
        self.openWelcomeApp = getattr(config, "open_welcome_app_on_start")
        self.welcomeCheckbox.set_active(self.openWelcomeApp)

    def onCheckboxPress(self, widget):
        self.openWelcomeApp = widget.get_active()

    def onCellEdited(self, widget, path, newText):
        liststore = widget.get_model()
        columnTitle = widget.get_cursor()[1].get_title()
        column = 0 if columnTitle == "Key" else 1
        oldText = liststore[path][column]
        self.keybindsChanges.append((path,column,oldText))
        liststore[path][column] = newText

    def onEntryEdited(self, widget):
        element = widget
        while not isinstance(element,Gtk.ScrolledWindow):
            element = element.get_parent()
        if element.get_name() == "windowPage":
            self.windowChanges.append((widget, self.lastEntryText))
        else:
            self.othersChanges.append((widget, self.lastEntryText))
        self.lastEntryText = widget.get_text()


    def onEntryFocus(self, widget, focus):
        self.lastEntryText = widget.get_text()

    def onAddKeybind(self, widget):
        liststore = widget.get_model()
        liststore.append([])
        path = Gtk.TreePath(len(liststore)-1)
        column = widget.get_columns()[0]
        widget.set_cursor(path,column,start_editing=True)

    def onDeleteKeybind(self, widget):
        if self.selected is not None:
            row = widget[self.selectedRow][:2]
            self.keybindsChanges.append((self.selectedRow, row))
            widget.remove(self.selected)

    def onSelectionChange(self, widget):
        try:
            self.selected = widget.get_selected()[1]
            self.selectedRow = widget.get_selected_rows()[1][0].get_indices()[0]
        except:
            return

    def onSaveConfig(self, widget):
        with open(self.configFile, "r") as configFile:
            lines = configFile.readlines()

        newConfig = []
        keybinds = False
        for line in lines:
            stripedLine = line.strip()
            if stripedLine:
                if stripedLine.startswith("keybinds = ["):
                    keybinds = True
                    newConfig.append(line)

                    for row in self.keybindsListstore:
                        key, binding = row[:2]
                        try:
                            binding = int(binding)
                        except:
                            binding = binding
                        newConfig.append(f"    [MOD, {key!r}, {binding!r}],\n")
                    continue

                if keybinds:
                    if stripedLine.startswith("]"):
                        newConfig.append("]\n")
                        keybinds = False
                    continue

                variable = line.split()[0]
                if variable in self.entryBuffers.keys():
                    value = self.entryBuffers[variable].get_text()
                    try:
                        value = int(value)
                    except:
                        value = value
                    newConfig.append(f"{variable} = {value!r}\n")
                    continue
                if variable.startswith("wallpaper"):
                    path = self.entryBuffers["wallpaperPath"].get_text()
                    app = self.entryBuffers["wallpaperMode"].get_text()
                    newConfig.append(f"{variable} = [{path!r}, {app!r}]\n")
                    continue
                if variable.startswith("open_welcome_app_on_start"):
                    newConfig.append(f"{variable} = {self.openWelcomeApp}\n")
                    continue
            newConfig.append(line)

        with open(self.configFile, 'w') as file:
            file.writelines(newConfig)

    def onUndoChange(self, widget):
        tab = widget.get_visible_child().get_name()
        match tab:
            case "keybindsPage":
                if len(self.keybindsChanges) > 0:
                    row = self.keybindsChanges.pop()
                    if len(row) == 3:
                        self.keybindsListstore[row[0]][row[1]] = row[2]
                    else:
                        self.keybindsListstore.insert(row[0], row[1])
            case "windowPage":
                if len(self.windowChanges) > 0:
                    row = self.windowChanges.pop()
                    entry = row[0]
                    text = row[1]
                    entry.set_text(text)
            case "othersPage":
                if len(self.othersChanges) > 0:
                    row = self.othersChanges.pop()
                    entry = row[0]
                    text = row[1]
                    entry.set_text(text)

    def onResetConfig(self, widget):
        self.keybindsListstore.clear()
        self.loadModel(self.keybindsListstore, config.keybinds)
        for key in self.entryBuffers.keys():
            if key.startswith("wallpaper"):
                continue
            self.loadBuffer(key)
        self.loadWallpaperBuffers()
        self.keybindsChanges = []
        self.windowChanges = []
        self.othersChanges = []


if __name__ == "__main__":
    main = ConfigApp()
    Gtk.main()