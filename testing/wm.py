import logging
from systemd.journal import JournalHandler
import xcffib
import xcffib.xproto
from xcffib.xproto import EventMask
from config import keybinds, wallpaper
from utils import Utils
import signal
import subprocess as sp


class WindowManager:
    def __init__(self):
        self.conn = xcffib.connect()
        self.screen = self.conn.get_setup().roots[0]
        self.root = self.screen.root
        self.utils = Utils(self.conn)
        self.windows = []
        self.focus_idx = 0
        self.wm_protocols = self.get_atom("WM_PROTOCOLS")
        self.wm_delete_window = self.get_atom("WM_DELETE_WINDOW")
        #log.warning(f"window -> atoms ids protocols:{self.wm_protocols}; delete:{self.wm_delete_window}")

        try:
            log.warning("Start init process")
            self.conn.core.ChangeWindowAttributesChecked(
                self.root,
                xcffib.xproto.CW.EventMask,
                [EventMask.SubstructureNotify | 
                 EventMask.SubstructureRedirect | 
                 EventMask.EnterWindow],
            ).check()
            log.warning("Init process done")
        except:
            log.warning("Another window manager is already running.")
            exit(1)

        self.conn.flush()

    
    def reload_config(self):
        import importlib
        importlib.reload(keybinds)


    def run(self):
        """Main event loop."""
        
        wall, wall_mode = wallpaper
        try:
            sp.run(["feh", f"--bg-{wall_mode}", wall])
        except Exception as e:
            log.warning(f"Error while setting a wallpaper: {e}")

        for mod, key, _ in keybinds:
            keycode = self.utils.get_keycode(Utils.string_to_keysym(key))
            modifier = getattr(xcffib.xproto.KeyButMask, mod, 0)

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
                # log.warning("Getting an event")
                event = self.conn.wait_for_event()
                # log.warning(f"Handling an event {event}")
                self.handle_event(event)
            except Exception as e:
                log.error(f"Main loop: {e}")
                break 


    def handle_event(self, event):
        """Dispatch X events."""
        if isinstance(event, xcffib.xproto.MapRequestEvent):
            log.warning(f"MapRequestEvent for a window: {event.window}")
            self.manage_window(event.window)
        if isinstance(event, xcffib.xproto.KeyPressEvent):
            log.warning(f"Keypress: {event}")
            self.handle_keypress(event)
        if isinstance(event, xcffib.xproto.EnterNotifyEvent):
            log.warning(f"Mouse entered window: {event.event}")
            self.update_focus(event.event)
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
            self.conn.core.ChangeWindowAttributes(
                window,
                xcffib.xproto.CW.EventMask,
                [xcffib.xproto.EventMask.EnterWindow]
            )
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
            self.focus_idx %= (len(self.windows) if self.windows else 1)

            try:
                reply = self.conn.core.GetProperty(
                    False, window, self.wm_protocols, xcffib.xproto.Atom.ATOM, 0, 32
                ).reply()

                if self.wm_delete_window in reply.value.to_atoms():
                    data = xcffib.xproto.ClientMessageData.synthetic([self.wm_delete_window, 0, 0, 0, 0])
                    # data = xcffib.xproto.ClientMessageData()
                    # data.data32 = [self.wm_delete_window, xcffib.xproto.Time.CurrentTime, 0, 0, 0]
                    event = xcffib.xproto.ClientMessageEvent.synthetic(
                        format=32,
                        window=window, 
                        type=self.wm_protocols,
                        data=data
                    )
                    self.conn.core.SendEvent(False, window, xcffib.xproto.EventMask.NoEvent, event.pack())
                else:
                    self.conn.core.KillClient(window)
            except Exception as e:
                log.warning(f"Error while killing a window: {e}")
                self.conn.core.KillClient(window)

        self.conn.flush()
        self.arrange_windows()


    def handle_action(self, function):
        if function == "NEXT_WINDOW":
            if len(self.windows) <= 1: return 

            self.focus_idx = (self.focus_idx + 1) % len(self.windows)
            self.conn.core.SetInputFocus(xcffib.xproto.InputFocus.PointerRoot, self.windows[self.focus_idx], xcffib.xproto.Time.CurrentTime)
            self.conn.flush()

        if function == "PREVIOUS_WINDOW":
            if len(self.windows) <= 1: return 

            self.focus_idx = (self.focus_idx - 1) % len(self.windows)
            self.conn.core.SetInputFocus(xcffib.xproto.InputFocus.PointerRoot, self.windows[self.focus_idx], xcffib.xproto.Time.CurrentTime)
            self.conn.flush()

        if function == "CLOSE":
            self.cleanup_window(self.windows[self.focus_idx])
            # self.arrange_windows()
            # self.conn.flush()

        if function == "RELOAD":
            self.reload_config()

        if function == "EXIT":
            log.warning("Exiting window manager")
            self.cleanup()


    def handle_keypress(self, event):
        """Handle keypress events based on the configuration."""
        for modifier, key, function in keybinds:
            keycode = self.utils.get_keycode(Utils.string_to_keysym(key))
            modifier = getattr(xcffib.xproto.KeyButMask, modifier, 0)

            if keycode == event.detail and modifier == event.state:
                try:
                    sp.Popen(function)
                except:
                    self.handle_action(function)

    
    def get_atom(self, name):
        return self.conn.core.InternAtom(False, len(name), name).reply().atom


    def cleanup(self):
        """Cleanup when exiting."""
        self.conn.disconnect()
        print("Exiting window manager.")
        exit()

import os
import time
if __name__ == "__main__":
    log = logging.getLogger('demo')
    log.addHandler(JournalHandler())
    log.setLevel(logging.INFO)
    log.warning("Starting the Window Manager")
    #sp.Popen(["export", "DISPLAY=:1"])
    #try:
    #    xephyr_process = sp.Popen(["Xephyr", ":1", "-screen", "1280x720", "-ac"])
    #except Exception as e:
    #    log.warning(f"Error while initializing xephyr {e}")
    #time.sleep(2)
    wm = WindowManager()
    wm.run()
    #xephyr_process.terminate()
