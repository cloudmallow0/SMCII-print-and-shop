LIGHT = {
    "PURPLE": "#7051B8",
    "DARK_PURPLE": "#503786",
    "LIGHT_PURPLE": "#F0EBF9",
    "WHITE": "#FFFFFF",
    "SURFACE": "#FFFFFF",
    "BG": "#F5F5F8",
    "TEXT": "#292536",
    "GRAY": "#777382",
    "BORDER": "#E2DFE9",
    "ENTRY_BORDER": "#CFC9DD",
    "GREEN": "#32845A",
    "RED": "#B74747",
    "SIDEBAR_BG": "#29213B",
    "STRIPE": "#F7F4FC",
    "BLUE": "#2E86AB",
    "ORANGE": "#E08E2B",
    "SELECT": "#DED3F4",
    "TINT_PURPLE": "#EDE6F9",
    "TINT_BLUE": "#E3F0FA",
    "TINT_ORANGE": "#FFF1DC",
    "TINT_GREEN": "#DDF3E7",
    "TINT_RED": "#F8E3E3",
    "TINT_GRAY": "#EEEDF2",
}

DARK = {
    "PURPLE": "#7C5CC4",
    "DARK_PURPLE": "#9479DA",
    "LIGHT_PURPLE": "#2F2644",
    "WHITE": "#FFFFFF",
    "SURFACE": "#221E2E",
    "BG": "#17141F",
    "TEXT": "#EDEAF5",
    "GRAY": "#A19CB3",
    "BORDER": "#352F45",
    "ENTRY_BORDER": "#4A4260",
    "GREEN": "#3FA371",
    "RED": "#C95555",
    "SIDEBAR_BG": "#100D17",
    "STRIPE": "#1D1927",
    "BLUE": "#3D93BA",
    "ORANGE": "#DC9340",
    "SELECT": "#4A3A73",
    "TINT_PURPLE": "#35294F",
    "TINT_BLUE": "#1F3442",
    "TINT_ORANGE": "#3F2F1B",
    "TINT_GREEN": "#1D3A2B",
    "TINT_RED": "#412324",
    "TINT_GRAY": "#2E2A3A",
}

PALETTES = {"light": LIGHT, "dark": DARK}


class Theme:

    def __init__(self, mode="light"):
        self.mode = "light"
        self.apply(mode)

    def apply(self, mode):
        if mode not in PALETTES:
            mode = "light"

        self.mode = mode

        for name, value in PALETTES[mode].items():
            setattr(self, name, value)