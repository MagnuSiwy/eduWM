import logging
from systemd.journal import JournalHandler
import xcffib
import xcffib.xproto
from xcffib.xproto import EventMask
from utils import Utils
from window import Window
import subprocess as sp
import importlib
import config
import os


class WindowManager:
    def __init__(self):
        try:
            self.conn = xcffib.connect()
        except Exception as e:
            log.error(f"Cannot create the connection to X server: {e}")
        self.screen = self.conn.get_setup().roots[0]
        self.root = self.screen.root
        self.utils = Utils(self.conn, self.screen, self.root)
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
            log.error("Another window manager is already running.")
            exit(1)

        self.conn.flush()

    
    def reload_config(self):
        importlib.reload(config)
        self.rearrange_windows()

    
    def wallpaper_setup(self):
        wall, wall_mode = config.wallpaper
        try:
            self.utils.set_wallpaper(wall)
            #sp.run(["feh", f"--bg-{wall_mode}", wall])
        except Exception as e:
            log.error(f"Error while setting a wallpaper: {e}")
            sp.run(["feh", f"--bg-{wall_mode}", wall])


    def launch_welcome_app(self):
        try:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../UIapps/welcomeWindow.py"))
            sp.Popen(["python3", script_path], start_new_session = True)
        except Exception as e:
            log.error(f"Error while opening the welcome app: {e}")


    def launch_config_app(self):
        try:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../UIapps/eduWMconfig.py"))
            sp.Popen(["python3", script_path], start_new_session = True)
        except Exception as e:
            log.error(f"Error while opening the config app: {e}")


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

        if config.open_welcome_app_on_start:
            self.launch_welcome_app()

        while True:
            try:
                event = self.conn.wait_for_event()
                self.handle_event(event)
            except Exception as e:
                log.error(f"Main loop error: {e}")
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
            try:
                self.update_focus(event.event, self.workspace_windows[self.focus_idx].window if self.workspace_windows else None)
            except:
                self.update_focus(event.event)
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
            # self.focus_idx = len(self.workspace_windows) - 1
            self.arrange_windows()

    
    def rearrange_windows(self):
        """Rearrange windows on all workspaces"""
        workspaces = set()
        for win in self.windows:
            workspaces.add(win.workspace)

        workspace_wins = []
        for i in workspaces:
            for win in self.windows:
                if win.workspace == i:
                    workspace_wins.append(win)
            self.arrange_windows(workspace_wins)
            workspace_wins = []


    def arrange_windows(self, workspace_wins = []):
        """Tile managed windows."""
        if not workspace_wins:
            if not self.workspace_windows:
                return
            workspace_wins = self.workspace_windows

        margin_out = config.margin_out
        margin_in = config.margin_in
        border_size = config.border_size
        layout = config.layout

        if layout == "columns":
            width = ((self.screen.width_in_pixels - 2 * margin_out) // len(workspace_wins)) - margin_in # (len(self.windows) + 1) * margin
            height = self.screen.height_in_pixels - 2 * margin_out

            for i, win in enumerate(workspace_wins):
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
            height = ((self.screen.height_in_pixels - 2 * margin_out) // len(workspace_wins)) - margin_in

            for i, win in enumerate(workspace_wins):
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

        self.focus_idx = min(self.focus_idx, len(self.workspace_windows))
        self.conn.flush()


    def change_border_color(self, window, color):
        border_color = int(color, 16)
        self.conn.core.ChangeWindowAttributes(
            window,
            xcffib.xproto.CW.BorderPixel,
            [border_color]
        )


    def update_focus(self, window, prev_win = None):
        """Update the focused window"""
        if prev_win:
            self.change_border_color(prev_win, config.border_color)
        
        windows = [win.window for win in self.workspace_windows]
        if window in windows:
            self.focus_idx = windows.index(window)
            log.info(f"Focus changed to {window}")

            self.change_border_color(window, config.border_color_active)

            self.conn.core.SetInputFocus(
                xcffib.xproto.InputFocus.PointerRoot, 
                window, 
                xcffib.xproto.Time.CurrentTime
            )

            self.conn.flush()
        

    def cleanup_window(self, window):
        """Destroy a window"""
        # If the functions gets a call from the event, get a window object out of window number
        if not isinstance(window, Window):
            for win in self.windows:
                if win.window == window:
                    window = win
                    break

        if window in self.workspace_windows: 
            self.windows.remove(window)
            self.workspace_windows.remove(window)
            self.focus_idx %= max(1, len(self.workspace_windows))

            reply = self.conn.core.GetProperty(
                False, 
                window.window, 
                self.wm_protocols, 
                xcffib.xproto.Atom.ATOM, 
                0, 
                32
            ).reply()

            if self.wm_delete_window in reply.value.to_atoms():
                data = xcffib.xproto.ClientMessageData.synthetic(
                    [self.wm_delete_window, 0, 0, 0, 0], 
                    "I" * 5
                )
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
                    event.pack()
                )
            else:
                # log.info(f"Killed a window")
                self.conn.core.KillClient(window.window)

        self.conn.flush()
        self.arrange_windows()


    def handle_action(self, function):
        if isinstance(function, int) and function != self.curr_workspace:
            self.curr_workspace = function % 10
            self.change_workspace(function % 10)

        elif function == "NEXT_WINDOW":
            if len(self.workspace_windows) <= 1: return 

            prev_win = self.workspace_windows[self.focus_idx].window
            self.focus_idx += 1
            self.focus_idx %= len(self.workspace_windows)
            self.update_focus(self.workspace_windows[self.focus_idx].window, prev_win)

        elif function == "PREVIOUS_WINDOW":
            if len(self.workspace_windows) <= 1: return 

            prev_win = self.workspace_windows[self.focus_idx].window
            self.focus_idx -= 1
            self.focus_idx %= len(self.workspace_windows)
            self.update_focus(self.workspace_windows[self.focus_idx].window, prev_win)

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

        elif function == "CONFIG_APP":
            self.launch_config_app()

        else:
            log.error("Incorrect action")


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