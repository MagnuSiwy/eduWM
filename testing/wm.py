import logging
from systemd.journal import JournalHandler
import xcffib
import xcffib.xproto
from xcffib.xproto import EventMask
import config
from utils import Utils
from window import Window
import subprocess as sp
import importlib


class WindowManager:
    def __init__(self):
        try:
            self.conn = xcffib.connect()
        except Exception as e:
            log.error(f"Cannot create the connection to X server: {e}")
        self.screen = self.conn.get_setup().roots[0]
        self.root = self.screen.root
        self.utils = Utils(self.conn)
        self.windows = []
        self.keybinds = []
        self.focus_idx = 0
        self.curr_workspace = 1
        self.workspace_windows = []
        self.wm_protocols = self.get_atom("WM_PROTOCOLS")
        self.wm_delete_window = self.get_atom("WM_DELETE_WINDOW")
        #log.info(f"window -> atoms ids protocols:{self.wm_protocols}; delete:{self.wm_delete_window}")

        try:
            log.info("Start init process")
            self.conn.core.ChangeWindowAttributesChecked(
                self.root,
                xcffib.xproto.CW.EventMask,
                [EventMask.SubstructureNotify | 
                 EventMask.SubstructureRedirect | 
                 EventMask.EnterWindow],
            ).check()
            log.info("Init process done")
        except:
            log.info("Another window manager is already running.")
            exit(1)

        self.conn.flush()

    
    def reload_config(self):
        importlib.reload(config)

    
    def wallpaper_setup(self):
        wall, wall_mode = config.wallpaper
        try:
            sp.run(["feh", f"--bg-{wall_mode}", wall])
        except Exception as e:
            log.error(f"Error while setting a wallpaper: {e}")


    def keybinds_setup(self):
        self.keybinds = []
        for mod, key, command in config.keybinds:
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

            self.keybinds.append((keycode, modifier, command))
        
        self.conn.flush()


    def run(self):
        """Main event loop."""
        self.wallpaper_setup()
        self.keybinds_setup()

        while True:
            try:
                # log.info("Getting an event")
                event = self.conn.wait_for_event()
                # log.info(f"Handling an event {event}")
                self.handle_event(event)
            except Exception as e:
                log.error(f"Main loop: {e}")
                break 


    def handle_event(self, event):
        """Dispatch X events."""
        if isinstance(event, xcffib.xproto.MapRequestEvent):
            log.info(f"MapRequestEvent for a window: {event.window}")
            self.manage_window(event.window)
        if isinstance(event, xcffib.xproto.KeyPressEvent):
            log.info(f"Keypress: {event}")
            self.handle_keypress(event)
        if isinstance(event, xcffib.xproto.EnterNotifyEvent):
            log.info(f"Mouse entered window: {event.event}")
            self.update_focus(event.event)
        # if isinstance(event, xcffib.xproto.ConfigureRequestEvent):
        #     log.info(f"Configure request for a window: {event.window}")
        #     self.arrange_windows()
        if isinstance(event, xcffib.xproto.DestroyNotifyEvent):
            log.info(f"Unmap window: {event.window}")
            self.cleanup_window(event.window)


    def manage_window(self, window):
        """Add and arrange a new window."""
        attr = self.conn.core.GetWindowAttributes(
            window
        ).reply()

        if attr.override_redirect:
            return 
        
        if window not in [win.window for win in self.windows]:
            log.info(f"Mapping window: {window}")
            self.conn.core.ChangeWindowAttributes(
                window,
                xcffib.xproto.CW.EventMask,
                [xcffib.xproto.EventMask.EnterWindow]
            )
            self.conn.core.MapWindow(window)
            window_obj = Window(window, self.curr_workspace)
            self.windows.append(window_obj)
            self.workspace_windows.append(window_obj)
            self.focus_idx = len(self.workspace_windows) - 1
            self.arrange_windows()


    def arrange_windows(self):
        """Tile all managed windows."""
        if not self.workspace_windows:
            return

        margin_out = config.margin_out
        margin_in = config.margin_in
        border_size = config.border_size
        layout = config.layout

        if layout == "columns":
            width = ((self.screen.width_in_pixels - 2 * margin_out) // len(self.workspace_windows)) - margin_in # (len(self.windows) + 1) * margin
            height = self.screen.height_in_pixels - 2 * margin_out

            for i, win in enumerate(self.workspace_windows):
                x = i * width + margin_out + i * margin_in
                y = margin_out
                win.setSize(width, height)
                win.setPosition(x, y)
                self.conn.core.ConfigureWindow(
                    win.window,
                    xcffib.xproto.ConfigWindow.X | 
                    xcffib.xproto.ConfigWindow.Y |
                    xcffib.xproto.ConfigWindow.Width | 
                    xcffib.xproto.ConfigWindow.Height |
                    xcffib.xproto.ConfigWindow.BorderWidth,
                    [x, y, width, height, border_size]
                )

        elif layout == "rows":
            width = self.screen.width_in_pixels - 2 * margin_out
            height = ((self.screen.height_in_pixels - 2 * margin_out) // len(self.workspace_windows)) - margin_in

            for i, win in enumerate(self.workspace_windows):
                x = margin_out
                y = i * height + margin_out + i * margin_in
                win.setSize(width, height)
                win.setPosition(x, y)
                self.conn.core.ConfigureWindow(
                    win.window,
                    xcffib.xproto.ConfigWindow.X | 
                    xcffib.xproto.ConfigWindow.Y |
                    xcffib.xproto.ConfigWindow.Width | 
                    xcffib.xproto.ConfigWindow.Height |
                    xcffib.xproto.ConfigWindow.BorderWidth,
                    [x, y, width, height, border_size]
                )
        
        self.conn.flush()


    def change_workspace(self, workspace):
        self.workspace_windows = []

        for window in self.windows:
            if window.workspace != workspace:
                self.conn.core.UnmapWindow(window.window)
            else:
                self.workspace_windows.append(window)
                self.conn.core.MapWindow(window.window)

        if self.workspace_windows:
            self.update_focus(self.workspace_windows[0].window)        
        self.conn.flush()


    def move_mouse(self, window):
        """Move the mouse pointer to the center of the window."""
        geometry = self.conn.core.GetGeometry(window).reply()
        x, y, width, height = geometry.x, geometry.y, geometry.width, geometry.height

        center_x = x + width // 2
        center_y = y + height // 2

        log.info("Move the mouse")

        self.conn.core.WarpPointer(
            0,
            0,
            0, 0, 0, 0, 
            center_x, 
            center_y
        )

        self.conn.flush()


    def update_focus(self, window):
        """Update the focused window"""
        windows = [win.window for win in self.workspace_windows]
        if window in windows:
            self.focus_idx = windows.index(window)
            log.info(f"Focus changed to {window}")

            self.conn.core.SetInputFocus(
                xcffib.xproto.InputFocus.PointerRoot, 
                window, 
                xcffib.xproto.Time.CurrentTime
            )

            self.conn.flush()
        

    def cleanup_window(self, window):
        """Destroy a window"""
        if not isinstance(window, Window):
            for win in self.windows:
                if win.window == window:
                    window = win
                    break

        if window in self.workspace_windows: 
            self.windows.remove(window)
            self.workspace_windows.remove(window)
            self.focus_idx %= max(1, len(self.workspace_windows))

            try:
                reply = self.conn.core.GetProperty(
                    False, window.window, self.wm_protocols, 
                    xcffib.xproto.Atom.ATOM, 
                    0, 
                    32
                ).reply()

                if self.wm_delete_window in reply.value.to_atoms():
                    data = xcffib.xproto.ClientMessageData.synthetic(
                        [self.wm_delete_window, 0, 0, 0, 0])
                    event = xcffib.xproto.ClientMessageEvent.synthetic(
                        format=32,
                        window=window.window, 
                        type=self.wm_protocols,
                        data=data
                    )
                    self.conn.core.SendEvent(
                        False, 
                        window.window, 
                        xcffib.xproto.EventMask.NoEvent, 
                        event.pack())
                else:
                    self.conn.core.KillClient(window.window)
            except Exception as e:
                log.error(f"Error while killing a window: {e}")
                self.conn.core.KillClient(window.window)

        self.conn.flush()
        self.arrange_windows()


    def handle_action(self, function):
        if isinstance(function, int) and function != self.curr_workspace:
            self.curr_workspace = function % 10
            self.change_workspace(function % 10)

        elif function == "NEXT_WINDOW":
            if len(self.workspace_windows) <= 1: return 

            self.focus_idx += 1
            self.focus_idx %= len(self.workspace_windows)
            self.move_mouse(self.workspace_windows[self.focus_idx].window)
            self.update_focus(self.workspace_windows[self.focus_idx].window)

        elif function == "PREVIOUS_WINDOW":
            if len(self.workspace_windows) <= 1: return 

            self.focus_idx -= 1
            self.focus_idx %= len(self.workspace_windows)
            self.move_mouse(self.workspace_windows[self.focus_idx].window)
            self.update_focus(self.workspace_windows[self.focus_idx].window)

        elif function == "CLOSE":
            if self.workspace_windows:
                self.cleanup_window(self.workspace_windows[self.focus_idx])

        elif function == "RELOAD":
            self.reload_config()
            self.wallpaper_setup()
            self.keybinds_setup()

        elif function == "EXIT":
            log.info("Exiting window manager")
            self.cleanup()

        else:
            log.info("Incorrect action")


    def handle_keypress(self, event):
        """Handle keypress events based on the configuration."""
        for mod, key, command in self.keybinds:
            if mod == event.detail and key == event.state:
                try:
                    sp.Popen(command, stdout=sp.DEVNULL, stderr=sp.DEVNULL)
                except:
                    self.handle_action(command)
    
    
    def get_atom(self, name):
        return self.conn.core.InternAtom(False, len(name), name).reply().atom


    def cleanup(self):
        """Cleanup when exiting."""
        self.conn.disconnect()
        log.info("Exiting window manager.")
        exit()



if __name__ == "__main__":
    log = logging.getLogger('demo')
    log.addHandler(JournalHandler())
    log.setLevel(logging.INFO)
    log.info("Starting the Window Manager")
    wm = WindowManager()
    wm.run()