import xpybutil
import xpybutil.keybind
import xcffib
import xcffib.xproto
from PIL import Image


class Utils:
    def __init__(self, conn, screen, root):
        self.conn = conn
        self.screen = screen
        self.root = root
        self.min_keycode = self.conn.get_setup().min_keycode
        self.max_keycode = self.conn.get_setup().max_keycode
        self.keyboard_mapping = self.conn.core.GetKeyboardMapping(
            self.min_keycode,
            self.max_keycode - self.min_keycode + 1
        ).reply()


    def string_to_keysym(string):
        return xpybutil.keysymdef.keysyms[string]


    def get_keysym(self, keycode, keysym_offset):
        """Get a keysym from a keycode"""
        keysyms_per_keycode = self.keyboard_mapping.keysyms_per_keycode

        return self.keyboard_mapping.keysyms[(keycode - self.min_keycode) * keysyms_per_keycode + keysym_offset]


    def get_keycode(self, keysym):
        """Get a keycode from a keysym"""
        keysyms_per_keycode = self.keyboard_mapping.keysyms_per_keycode

        for keycode in range(self.min_keycode, self.max_keycode + 1):
            for keysym_offset in range(0, keysyms_per_keycode):
                if self.get_keysym(keycode, keysym_offset) == keysym:
                    return keycode

        return None
    

    def set_wallpaper(self, image_path, option="contain"):
        # Load the image
        img = Image.open(image_path).convert("RGB")

        # Resize the image while maintaining the aspect ratio
        if option == "contain":
            img.thumbnail((self.screen.width_in_pixels, self.screen.height_in_pixels))
            new_img = Image.new("RGB", (self.screen.width_in_pixels, self.screen.height_in_pixels), (0, 0, 0))
            new_img.paste(
                img, 
                ((self.screen.width_in_pixels - img.width) // 2, (self.screen.height_in_pixels - img.height) // 2)
            )
            img = new_img

        # Convert image to raw pixel data
        pixel_data = img.tobytes("raw", "BGRX")

        # Create a pixmap
        pixmap = self.conn.generate_id()
        self.conn.core.CreatePixmap(
            self.screen.root_depth,  # Depth must match screen depth
            pixmap,
            self.root,
            self.screen.width_in_pixels,
            self.screen.height_in_pixels
        )

        # Create a graphics context
        gc = self.conn.generate_id()
        self.conn.core.CreateGC(gc, pixmap, 0, [])

        # Transfer image data to pixmap
        self.conn.core.PutImage(
            xcffib.xproto.ImageFormat.XYPixmap,
            pixmap,
            gc,
            self.screen.width_in_pixels,
            self.screen.height_in_pixels,
            0,
            0,
            0,
            self.screen.root_depth,
            pixel_data
        )

        # Set pixmap as root background
        self.conn.core.ChangeWindowAttributes(
            self.root,
            xcffib.xproto.CW.BackPixmap,
            [pixmap]
        )

        # Free the pixmap and graphics context
        self.conn.core.FreePixmap(pixmap)
        self.conn.core.FreeGC(gc)

        # Clear the area to redraw the root window
        self.conn.core.ClearArea(
            0,
            self.root,
            0,
            0,
            self.screen.width_in_pixels,
            self.screen.height_in_pixels
        )

        # Flush all changes
        self.conn.flush()
