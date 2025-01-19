import gi
import subprocess
#switch installed programs page to recomennded apps
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class Main():
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("welcomeWindow.glade")
        self.builder.connect_signals(self)

        window = self.builder.get_object("mainWindow")
        window.show()

    def onQuit(widget, arg):
        Gtk.main_quit()

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
        subprocess.Popen(["python3", "eduWMconfig.py"])


if __name__ == "__main__":
    main = Main()
    Gtk.main()