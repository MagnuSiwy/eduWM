import gi
import subprocess
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk


class WelcomeApp():
    def __init__(self):
        self.builder = Gtk.Builder()
        self.path = os.path.dirname(__file__)
        self.builder.add_from_file(os.path.join(self.path, "welcomeWindow.glade"))
        self.builder.connect_signals(self)

        window = self.builder.get_object("mainWindow")
        window.set_deletable(False)
        window.set_type_hint(Gdk.WindowTypeHint.DIALOG)
        window.show()

    def onQuit(widget):
        Gtk.main_quit()
        return True

    def onPreviousClicked(self, widget):
        pages = widget.get_children()
        cur_page = widget.get_visible_child()
        i = pages.index(cur_page)
        if i == 0: return
        widget.set_visible_child(pages[i-1])

    def onNextClicked(self, widget):
        pages = widget.get_children()
        cur_page = widget.get_visible_child()
        i = pages.index(cur_page)
        if i == len(pages) - 1: return
        widget.set_visible_child(pages[i+1])

    def onRunConfigAppClicked(self, widget):
        subprocess.Popen(["python3", os.path.join(self.path, "eduWMconfig.py")])


if __name__ == "__main__":
    main = WelcomeApp()
    Gtk.main()