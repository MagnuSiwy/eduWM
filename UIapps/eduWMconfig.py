import gi
import config

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
# change wallpaper entry to two parts

class Window():
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("eduWMconfig.glade")
        self.builder.connect_signals(self)
        self.selected = None
        self.selectedRow = None
        self.keybindsChanges = []
        self.windowChanges = []
        self.othersChanges = []
        self.lastEntryText = None
        self.entryBuffers = { "margin_out": None, "margin_in": None, "layout": None, "border_size": None, "focus": None, "wallpaper": None }

        self.keybindsTreeView = self.builder.get_object("keybindsTreeView")
        self.keybindsListstore = self.builder.get_object("keybindsListstore")

        self.loadModel(self.keybindsListstore, config.keybinds)
        for key in self.entryBuffers.keys():
            self.loadBuffer(key)

        window = self.builder.get_object("mainWindow")
        window.show()

    def onQuit(widget, arg):
        Gtk.main_quit()

    def loadModel(self, liststore, data):
        for row in data:
            liststore.append([row[1],str(row[2])])

    def loadBuffer(self, key):
        buffer = self.builder.get_object(f"{key}Buffer")
        text = str(getattr(config, key))
        self.entryBuffers[key] = buffer
        buffer.set_text(text, len(text))

    def onCellEdited(self, widget, path, newText):
        liststore = widget.get_model()
        columnTitle = widget.get_cursor()[1].get_title()
        column = 0 if columnTitle == "Key" else 1
        oldText = liststore[path][column]
        self.keybindsChanges.append((path,column,oldText))
        liststore[path][column] = newText

    def onEntryEdited(self, widget):
        self.windowChanges.append((widget, self.lastEntryText))

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
        with open("test.py", "r") as configFile:
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
            newConfig.append(line)

        with open("test.py", 'w') as file:
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


if __name__ == "__main__":
    main = Window()
    Gtk.main()