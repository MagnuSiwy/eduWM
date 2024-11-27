import logging
from systemd.journal import JournalHandler
import xcffib
import xcffib.xproto
from xcffib.xproto import EventMask
from config import keybinds
from utils import KeyUtil
import signal
import subprocess as sp


class WindowManager:
    def __init__(self):
        self.conn = xcffib.connect()
        self.screen = self.conn.get_setup().roots[0]
        self.root = self.screen.root
        self.key_util = KeyUtil(self.conn)
        self.windows = []
        self.focus_idx = 0

        # self.conn.core.ChangeWindowAttributes(
        #     self.root,
        #     xcffib.xproto.CW.BackPixel,
        #     [0x00FF00]
        # )
        # self.conn.flush()

        # Set up event listening on the root window
        try:
            log.warning("Start init process")
            self.conn.core.ChangeWindowAttributesChecked(
                self.root,
                xcffib.xproto.CW.EventMask,
                [EventMask.SubstructureNotify | EventMask.SubstructureRedirect | EventMask.EnterWindow],
            ).check()
            log.warning("Init process done")
        except:
            log.warning("Another window manager is already running.")
            exit(1)

        self.conn.flush()


    def run(self):
        """Main event loop."""
        for bind in keybinds:
            keycode = self.key_util.get_keycode(KeyUtil.string_to_keysym(bind[1]))
            modifier = getattr(xcffib.xproto.KeyButMask, bind[0], 0)

            self.conn.core.GrabKeyChecked(
                False,
                self.root,
                modifier,
                keycode,
                xcffib.xproto.GrabMode.Async,
                xcffib.xproto.GrabMode.Async
            ).check()

        while True:
            try:
                log.warning("Getting an event")
                event = self.conn.wait_for_event()
                log.warning(f"Handling an event {event}")
                self.handle_event(event)
            except Exception as e:
                log.error(f"ERROR: {e}")
                break 
            # self.arrange_windows()
            # self.conn.flush()


    def handle_event(self, event):
        """Dispatch X events."""
        if isinstance(event, xcffib.xproto.MapRequestEvent):
            log.warning(f"MapRequestEvent for a window: {event.window}")
            self.manage_window(event.window)
        if isinstance(event, xcffib.xproto.KeyPressEvent):
            log.warning(f"Keypress: {event}")
            self.handle_keypress(event)
        if isinstance(event, xcffib.xproto.EnterNotifyEvent):
            log.warning(f"Mouse entered window: {event}")
            #self.update_focus(event.window)
        # if isinstance(event, xcffib.xproto.ConfigureRequestEvent):
        #     log.warning(f"Configure request for a window: {event.window}")
        #     self.arrange_windows()
        if isinstance(event, xcffib.xproto.DestroyNotifyEvent):
            log.warning(f"Unmap window: {event.window}")
            self.cleanup_window(event.window)


    def manage_window(self, window):
        """Add and arrange a new window."""
        attr = self.conn.core.GetWindowAttributes(
            window
        ).reply()

        if attr.override_redirect:
            return 
        
        if window not in self.windows:
            log.warning(f"Mapping window: {window}")
            self.conn.core.MapWindow(window)
            self.windows.insert(0, window)
            self.focus_idx = 0
            self.arrange_windows()


    def arrange_windows(self):
        """Tile all managed windows."""
        if not self.windows:
            return
        
        log.warning(f"Active windows {len(self.windows)}")
        log.warning(f"Active window {self.windows[0]}")

        margin = 10
        width = ((self.screen.width_in_pixels - margin) // len(self.windows)) - margin # (len(self.windows) + 1) * margin
        height = self.screen.height_in_pixels - 2 * margin
        border = 2

        for i, win in enumerate(self.windows):
            x = i * width + (i + 1) * margin
            y = margin
            self.conn.core.ConfigureWindow(
                win,
                xcffib.xproto.ConfigWindow.X | 
                xcffib.xproto.ConfigWindow.Y |
                xcffib.xproto.ConfigWindow.Width | 
                xcffib.xproto.ConfigWindow.Height,
                [x, y, width, height]
            )
        
        self.conn.flush()


    def update_focus(self, window):
        if window in self.windows:
            self.focus_idx = self.windows.index(window)
            log.warning(f"Focus changed to {window}")

            # self.conn.core.RaiseWindow(window)
            # self.conn.core.SetInputFocus(
            #     xcffib.xproto.InputFocus.PointerRoot, window, xcffib.xproto.Time.CurrentTime
            # )
            self.conn.flush()
        

    def cleanup_window(self, window):
        """Remove a window from management."""
        if window in self.windows: 
            self.windows.remove(window)
            self.focus_idx %= len(self.windows)

            try:
                attr = self.conn.core.GetWindowAttributes(window).reply()
                if attr.map_state != xcffib.xproto.MapState.Unmapped:
                    self.conn.core.DestroyWindow(window)
            except xcffib.ConnectionException as e:
                log.warning(f"Window {window} already destroyed: {e}")

        self.conn.flush()
        self.arrange_windows()


    def handle_action(self, function):
        if function == "NEXT_WINDOW":
            if len(self.windows) <= 1: return 

            self.focus_idx = (self.focus_idx + 1) % len(self.windows)
            self.conn.core.SetInputFocus(xcffib.xproto.InputFocus.PointerRoot, self.windows[self.focus_idx], xcffib.xproto.Time.CurrentTime)
            self.conn.core.RaiseWindow(self.windows[self.focus_idx])
            self.conn.flush()

        if function == "PREVIOUS_WINDOW":
            if len(self.windows) <= 1: return 

            self.focus_idx = (self.focus_idx - 1) % len(self.windows)
            self.conn.core.SetInputFocus(xcffib.xproto.InputFocus.PointerRoot, self.windows[self.focus_idx], xcffib.xproto.Time.CurrentTime)
            self.conn.core.RaiseWindow(self.windows[self.focus_idx])
            self.conn.flush()

        if function == "CLOSE":
            self.cleanup_window(self.windows[self.focus_idx])
            # self.arrange_windows()
            # self.conn.flush()

        if function == "EXIT":
            log.warning("Exiting window manager")
            self.cleanup()


    def handle_keypress(self, event):
        """Handle keypress events based on the configuration."""
        for modifier, key, function in keybinds:
            keycode = self.key_util.get_keycode(KeyUtil.string_to_keysym(key))
            modifier = getattr(xcffib.xproto.KeyButMask, modifier, 0)

            if keycode == event.detail and modifier == event.state:
                try:
                    sp.Popen(function)
                except:
                    self.handle_action(function)


    def cleanup(self):
        """Cleanup when exiting."""
        self.conn.disconnect()
        print("Exiting window manager.")
        exit()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: exit(0))
    log = logging.getLogger('demo')
    log.addHandler(JournalHandler())
    log.setLevel(logging.INFO)
    log.warning("Starting the Window Manager")
    wm = WindowManager()
    wm.run()

