import xpybutil
import xpybutil.keybind
import xcffib
import xcffib.xproto
from PIL import Image


class Utils:
    def __init__(self, conn):
        self.conn = conn
        self.min_keycode = self.conn.get_setup().min_keycode
        self.max_keycode = self.conn.get_setup().max_keycode
        self.keyboard_mapping = self.conn.core.GetKeyboardMapping(
            self.min_keycode,
            self.max_keycode - self.min_keycode + 1
        ).reply()


    def string_to_keysym(string):
        return xpybutil.keysymdef.keysyms[string]


    def get_keysym(self, keycode, keysym_offset):
        """
        Get a keysym from a keycode and state/modifier.

        Only a partial implementation. For more details look at Keyboards section in X Protocol:
        https://www.x.org/docs/XProtocol/proto.pdf

        :param keycode: Keycode of keysym
        :param keysym_offset: The modifier/state/offset we are accessing
        :returns: Keysym
        """

        keysyms_per_keycode = self.keyboard_mapping.keysyms_per_keycode

        return self.keyboard_mapping.keysyms[
            (keycode - self.min_keycode) * keysyms_per_keycode + keysym_offset
        ]


    def get_keycode(self, keysym):
        """
        Get a keycode from a keysym

        :param keysym: keysym you wish to convert to keycode
        :returns: Keycode if found, else None
        """

        keysyms_per_keycode = self.keyboard_mapping.keysyms_per_keycode

        for keycode in range(self.min_keycode, self.max_keycode + 1):
            for keysym_offset in range(0, keysyms_per_keycode):
                if self.get_keysym(keycode, keysym_offset) == keysym:
                    return keycode

        return None
    

    # def set_wallpaper(self, image_path):
    #     img = Image.open(image_path).convert("RGB")
    #     img = img.resize((self.screen.width_in_pixels, self.screen.height_in_pixels))
    #     pixel_data = img.tobytes("raw", "BGRX")

    #     pixmap = self.conn.generate_id()
    #     self.conn.core.CreatePixmap(
    #         self.screen.root_depth, 
    #         pixmap, 
    #         self.root, 
    #         self.screen.width_in_pixels, 
    #         self.screen.height_in_pixels
    #     )

    #     gc = self.conn.generate_id()
    #     self.conn.core.CreateGC(gc, pixmap, 0, [])

    #     self.conn.core.PutImage(
    #         xcffib.xproto.ImageFormat.ZPixmap,
    #         pixmap,
    #         gc,
    #         self.screen.width_in_pixels, 
    #         self.screen.height_in_pixels,
    #         0,
    #         0,
    #         0,
    #         24,
    #         pixel_data
    #     )

    #     self.conn.core.ChangeWindowAttributes(
    #         self.root,
    #         xcffib.xproto.CW.BackPixmap,
    #         [pixmap]
    #     )

    #     self.conn.core.FreePixmap(pixmap)
    #     self.conn.core.FreeGC(gc)

    #     self.conn.core.ClearArea(
    #         0,                      # Exposures (0 = don't generate)
    #         self.root,              # Drawable (root window)
    #         0,                      # X
    #         0,                      # Y
    #         self.screen.width_in_pixels,
    #         self.screen.height_in_pixels
    #     )

    #     self.conn.flush()