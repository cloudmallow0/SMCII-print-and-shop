
class Screen:
    def __init__(self, app):
        self.app = app

    @property
    def root(self):
        return self.app.root

    @property
    def theme(self):
        return self.app.theme

    @property
    def services(self):
        return self.app.services

    @property
    def printing(self):
        return self.app.printing

    @property
    def ui(self):
        return self.app.ui