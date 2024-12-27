class Window:
    def __init__(self, window, workspace):
        self.window = window
        self.workspace = workspace
        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0
    
    def setPosition(self, x, y):
        self.x = x
        self.y = y
    
    def setSize(self, width, height):
        self.width = width
        self.height = height
    
    def setWidth(self, new_width):
        self.width = new_width

    def setHeight(self, new_height):
        self.height = new_height
    
    def setWorkspace(self, new_workspace):
        self.workspace = new_workspace