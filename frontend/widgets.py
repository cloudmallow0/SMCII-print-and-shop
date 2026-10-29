import tkinter as tk
from tkinter import ttk
from datetime import datetime

from PIL import Image, ImageTk, ImageDraw, ImageFilter

from frontend.screen import Screen


class Widgets(Screen):

    LINE_IDLE = "#D6D1E3"

    def __init__(self, app):
        super().__init__(app)
        self.image_cache = {}   # also keeps PhotoImages alive so Tk doesn't drop them

    def darken(self, color, factor=0.82):
        r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
        return f"#{int(r * factor):02X}{int(g * factor):02X}{int(b * factor):02X}"

    def show_toast(self, title, message, color=None):
        color = color or self.theme.GREEN

        try:
            toast = tk.Toplevel(self.root)
            toast.overrideredirect(True)
            toast.attributes("-topmost", True)
            toast.configure(bg=color)

            inner = tk.Frame(toast, bg=self.theme.SURFACE, padx=18, pady=12)
            inner.pack(padx=(6, 0))

            tk.Label(
                inner, text=title, font=("Arial", 11, "bold"),
                bg=self.theme.SURFACE, fg=color, anchor="w"
            ).pack(anchor="w")

            tk.Label(
                inner, text=message, font=("Arial", 10),
                bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w", justify="left"
            ).pack(anchor="w", pady=(3, 0))

            toast.update_idletasks()

            x = self.root.winfo_rootx() + self.root.winfo_width() - toast.winfo_reqwidth() - 25
            y = self.root.winfo_rooty() + self.root.winfo_height() - toast.winfo_reqheight() - 45
            toast.geometry(f"+{x}+{y}")
            toast.after(4000, toast.destroy)

        except tk.TclError:
            pass

    def get_thumbnail(self, path, size):
        key = (path, size)

        if key in self.image_cache:
            return self.image_cache[key]

        try:
            picture = Image.open(path).convert("RGB")
            picture.thumbnail((size, size), Image.Resampling.LANCZOS)

            tile = Image.new("RGB", (size, size), (240, 235, 249))
            tile.paste(
                picture,
                ((size - picture.width) // 2, (size - picture.height) // 2)
            )

        except (OSError, ValueError):
            tile = Image.new("RGB", (size, size), (240, 235, 249))

            if size >= 80:
                draw = ImageDraw.Draw(tile)
                label = "No Image"
                box = draw.textbbox((0, 0), label)
                draw.text(
                    (
                        (size - (box[2] - box[0])) // 2,
                        (size - (box[3] - box[1])) // 2
                    ),
                    label,
                    fill=(119, 115, 130)
                )

        photo = ImageTk.PhotoImage(tile)
        self.image_cache[key] = photo
        return photo

    def make_label(self, parent, text, size=11, bold=False, color=None):
        return tk.Label(
            parent,
            text=text,
            font=("Arial", size, "bold" if bold else "normal"),
            bg=parent.cget("bg"),
            fg=color or self.theme.TEXT,
            anchor="w"
        )

    def make_entry(self, parent, width=35, show=None):
        return tk.Entry(
            parent,
            width=width,
            font=("Arial", 12),
            show=show,
            bg=self.theme.SURFACE,
            fg=self.theme.TEXT,
            insertbackground=self.theme.TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=self.theme.ENTRY_BORDER,
            highlightcolor=self.theme.PURPLE
        )

    def make_password_field(self, parent, ipady=9):
        box = tk.Frame(
            parent, bg=self.theme.SURFACE,
            highlightbackground=self.theme.ENTRY_BORDER, highlightthickness=1
        )

        entry = tk.Entry(
            box,
            font=("Arial", 12),
            show="*",
            bg=self.theme.SURFACE,
            fg=self.theme.TEXT,
            insertbackground=self.theme.TEXT,
            relief="flat",
            bd=0
        )
        entry.pack(side="left", fill="x", expand=True, ipady=ipady, padx=(8, 0))

        toggle = tk.Label(
            box, text="👁", font=("Segoe UI Emoji", 12),
            bg=self.theme.SURFACE, fg=self.theme.GRAY, cursor="hand2", padx=10
        )
        toggle.pack(side="right")

        def flip(event=None):
            if entry.cget("show") == "*":
                entry.config(show="")
                toggle.config(text="🙈", fg=self.theme.PURPLE)
            else:
                entry.config(show="*")
                toggle.config(text="👁", fg=self.theme.GRAY)

        toggle.bind("<Button-1>", flip)

        entry.bind(
            "<FocusIn>", lambda e: box.config(highlightbackground=self.theme.PURPLE)
        )
        entry.bind(
            "<FocusOut>", lambda e: box.config(highlightbackground=self.theme.ENTRY_BORDER)
        )

        return box, entry

    def make_line_entry(self, parent, ipady=9):
        box = tk.Frame(parent, bg=self.theme.SURFACE)

        entry = tk.Entry(
            box, font=("Arial", 12), bg=self.theme.SURFACE, fg=self.theme.TEXT,
            insertbackground=self.theme.TEXT, relief="flat", bd=0, highlightthickness=0
        )
        entry.pack(fill="x", ipady=ipady, padx=2)

        line = tk.Frame(box, bg=self.LINE_IDLE, height=2)
        line.pack(fill="x")

        entry.bind("<FocusIn>", lambda e: line.config(bg=self.theme.PURPLE))
        entry.bind("<FocusOut>", lambda e: line.config(bg=self.LINE_IDLE))
        return box, entry

    def make_line_password(self, parent, ipady=9):
        box = tk.Frame(parent, bg=self.theme.SURFACE)

        row = tk.Frame(box, bg=self.theme.SURFACE)
        row.pack(fill="x")

        entry = tk.Entry(
            row, font=("Arial", 12), show="*", bg=self.theme.SURFACE, fg=self.theme.TEXT,
            insertbackground=self.theme.TEXT, relief="flat", bd=0, highlightthickness=0
        )
        entry.pack(side="left", fill="x", expand=True, ipady=ipady, padx=2)

        toggle = tk.Label(
            row, text="👁", font=("Segoe UI Emoji", 12),
            bg=self.theme.SURFACE, fg=self.theme.GRAY, cursor="hand2", padx=6
        )
        toggle.pack(side="right")

        line = tk.Frame(box, bg=self.LINE_IDLE, height=2)
        line.pack(fill="x")

        def flip(event=None):
            if entry.cget("show") == "*":
                entry.config(show="")
                toggle.config(text="🙈", fg=self.theme.PURPLE)
            else:
                entry.config(show="*")
                toggle.config(text="👁", fg=self.theme.GRAY)

        toggle.bind("<Button-1>", flip)
        entry.bind("<FocusIn>", lambda e: line.config(bg=self.theme.PURPLE))
        entry.bind("<FocusOut>", lambda e: line.config(bg=self.LINE_IDLE))
        return box, entry

    def make_round_field(self, parent, password=False, height=44, radius=12):
        idle, active = self.theme.ENTRY_BORDER, self.theme.PURPLE

        box = tk.Canvas(
            parent, height=height, bg=self.theme.SURFACE, highlightthickness=0, bd=0
        )

        entry = tk.Entry(
            box, font=("Arial", 12), bg=self.theme.SURFACE, fg=self.theme.TEXT,
            insertbackground=self.theme.TEXT, relief="flat", bd=0, highlightthickness=0,
            show="*" if password else ""
        )

        right_space = 46 if password else 14
        entry.place(
            x=14, rely=0.5, anchor="w", relwidth=1,
            width=-(14 + right_space), height=height - 14
        )

        focus = {"on": False}

        def draw(event=None):
            w = box.winfo_width()
            h = height

            if w < 4:
                return

            r = radius
            points = [
                r, 1,  w - r, 1,  w - 1, 1,  w - 1, r,
                w - 1, h - r,  w - 1, h - 1,  w - r, h - 1,
                r, h - 1,  1, h - 1,  1, h - r,  1, r,  1, 1
            ]

            box.delete("border")
            box.create_polygon(
                points, smooth=True, fill=self.theme.WHITE, tags="border",
                outline=active if focus["on"] else idle,
                width=2 if focus["on"] else 1
            )
            box.tag_lower("border")

        def set_focus(value):
            focus["on"] = value
            draw()

        box.bind("<Configure>", draw)
        entry.bind("<FocusIn>", lambda e: set_focus(True))
        entry.bind("<FocusOut>", lambda e: set_focus(False))

        if password:
            toggle = tk.Label(
                box, text="👁", font=("Segoe UI Emoji", 12),
                bg=self.theme.SURFACE, fg=self.theme.GRAY, cursor="hand2"
            )
            toggle.place(relx=1, x=-12, rely=0.5, anchor="e")

            def flip(event=None):
                if entry.cget("show") == "*":
                    entry.config(show="")
                    toggle.config(text="🙈", fg=self.theme.PURPLE)
                else:
                    entry.config(show="*")
                    toggle.config(text="👁", fg=self.theme.GRAY)

            toggle.bind("<Button-1>", flip)

        return box, entry

    def make_check(self, parent, text, variable):
        row = tk.Frame(parent, bg=self.theme.SURFACE, cursor="hand2")

        box = tk.Canvas(
            row, width=20, height=20, bg=self.theme.SURFACE,
            highlightthickness=0, bd=0, cursor="hand2"
        )
        box.pack(side="left")

        label = tk.Label(
            row, text=text, font=("Arial", 10), bg=self.theme.SURFACE, fg=self.theme.GRAY,
            cursor="hand2"
        )
        label.pack(side="left", padx=(8, 0))

        def draw(*args):
            try:
                box.delete("all")
                on = variable.get()
                x1, y1, x2, y2, r = 2, 2, 18, 18, 5

                points = [
                    x1 + r, y1,  x2 - r, y1,  x2, y1,  x2, y1 + r,
                    x2, y2 - r,  x2, y2,  x2 - r, y2,  x1 + r, y2,
                    x1, y2,  x1, y2 - r,  x1, y1 + r,  x1, y1
                ]

                box.create_polygon(
                    points, smooth=True,
                    fill=self.theme.PURPLE if on else self.theme.SURFACE,
                    outline=self.theme.PURPLE if on else self.theme.ENTRY_BORDER,
                    width=2
                )

                if on:
                    box.create_line(
                        6, 10, 9, 13, 14, 7, fill=self.theme.WHITE, width=2,
                        capstyle="round", joinstyle="round"
                    )
            except tk.TclError:
                pass

        def toggle(event=None):
            variable.set(not variable.get())

        def hover(on):
            label.config(fg=self.theme.TEXT if on else self.theme.GRAY)

        for widget in (row, box, label):
            widget.bind("<Button-1>", toggle)
            widget.bind("<Enter>", lambda e: hover(True))
            widget.bind("<Leave>", lambda e: hover(False))

        variable.trace_add("write", draw)
        draw()
        return row

    def make_button(self, parent, text, command, width=22, color=None):
        color = color or self.theme.PURPLE
        hover = self.darken(color)

        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Arial", 11, "bold"),
            bg=color,
            fg=self.theme.WHITE,
            activebackground=hover,
            activeforeground=self.theme.WHITE,
            width=width,
            pady=10,
            bd=0,
            cursor="hand2"
        )

        button.bind("<Enter>", lambda e: button.config(bg=hover))
        button.bind("<Leave>", lambda e: button.config(bg=color))

        return button

    def make_card(self, parent):
        return tk.Frame(
            parent,
            bg=self.theme.SURFACE,
            padx=25,
            pady=22,
            highlightbackground=self.theme.BORDER,
            highlightthickness=1
        )

    def page_heading(self, title, subtitle=""):
        self.make_label(
            self.app.content_frame, title, 22, True
        ).pack(anchor="w", pady=(0, 5))

        if subtitle:
            self.make_label(
                self.app.content_frame, subtitle, 11, False, self.theme.GRAY
            ).pack(anchor="w", pady=(0, 22))

    def money(self, amount):
        return f"PHP {amount:,.2f}"

    def make_soft_background(self):
        base = Image.new("RGB", (300, 450), (252, 248, 251))
        draw = ImageDraw.Draw(base)

        blobs = [
            ((-60, 30, 150, 230), (255, 183, 208)),
            ((170, 60, 380, 250), (151, 226, 246)),
            ((60, 250, 300, 520), (216, 199, 246)),
            ((-80, 330, 120, 520), (255, 214, 190)),
        ]

        for box, color in blobs:
            draw.ellipse(box, fill=color)

        return base.filter(ImageFilter.GaussianBlur(40))

    def rounded_photo(self, picture, size, radius, backdrop_rgb):
        picture = picture.resize(size, Image.Resampling.LANCZOS).convert("RGBA")

        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, size[0] - 1, size[1] - 1), radius, fill=255
        )
        picture.putalpha(mask)

        backdrop = Image.new("RGBA", size, backdrop_rgb + (255,))
        backdrop.alpha_composite(picture)

        return ImageTk.PhotoImage(backdrop.convert("RGB"))

    def _mix(self, color_a, color_b, t):
        a = [int(color_a[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(color_b[i:i + 2], 16) for i in (1, 3, 5)]
        return "#%02X%02X%02X" % tuple(
            round(x + (y - x) * t) for x, y in zip(a, b)
        )

    def _round_rect(self, canvas, x1, y1, x2, y2, r, **kw):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kw)

    def status_style(self, status):
        return {
            "Pending": (self.theme.TINT_ORANGE, self.theme.ORANGE),
            "Printing": (self.theme.TINT_BLUE, self.theme.BLUE),
            "Ready for Pickup": (self.theme.TINT_GREEN, self.theme.GREEN),
            "Completed": (self.theme.TINT_GRAY, self.theme.GRAY),
        }.get(status, (self.theme.TINT_GRAY, self.theme.GRAY))

    def student_initials(self):
        return "".join(
            part[0] for part in str(self.app.current_name).split()[:2]
        ).upper() or "?"

    def avatar_image(self, path, size):
        key = ("avatar", path, size)

        if key in self.image_cache:
            return self.image_cache[key]

        try:
            img = Image.open(path).convert("RGBA")
            side = min(img.size)
            left, top = (img.width - side) // 2, (img.height - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((size, size), Image.LANCZOS)

            big = size * 4
            mask = Image.new("L", (big, big), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, big - 1, big - 1), fill=255)
            img.putalpha(mask.resize((size, size), Image.LANCZOS))

            photo = ImageTk.PhotoImage(img)
        except Exception:
            return None

        self.image_cache[key] = photo
        return photo

    def draw_avatar(self, canvas, size, path, initials, ring, fill, font_size):
        canvas.delete("all")
        pad = 3
        canvas.create_oval(
            pad, pad, size - pad, size - pad, fill=fill, outline=ring, width=3,
            tags="ring"
        )

        photo = self.avatar_image(path, size - pad * 2 - 4) if path else None

        if photo:
            canvas.create_image(size // 2, size // 2, image=photo)
            canvas.photo = photo
        else:
            canvas.create_text(
                size // 2, size // 2, text=initials, fill=self.theme.WHITE,
                font=("Arial", font_size, "bold")
            )

    def make_scroll_page(self, parent):
        holder = tk.Frame(parent, bg=self.theme.BG)
        holder.pack(fill="both", expand=True)

        canvas = tk.Canvas(holder, bg=self.theme.BG, highlightthickness=0)
        bar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=bar.set)
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=self.theme.BG)
        window = canvas.create_window((0, 0), window=inner, anchor="nw")
        state = {"bar": False}

        def fit(event=None):
            try:
                canvas.itemconfigure(window, width=canvas.winfo_width())
                canvas.configure(scrollregion=canvas.bbox("all"))
                needs_bar = inner.winfo_reqheight() > canvas.winfo_height()

                if needs_bar and not state["bar"]:
                    bar.pack(side="right", fill="y")
                    state["bar"] = True
                elif not needs_bar and state["bar"]:
                    bar.pack_forget()
                    canvas.yview_moveto(0)
                    state["bar"] = False
            except tk.TclError:
                pass

        inner.bind("<Configure>", fit)
        canvas.bind("<Configure>", fit)

        def on_wheel(event):
            try:
                if state["bar"] and canvas.winfo_exists():
                    canvas.yview_scroll(int(-event.delta / 120), "units")
            except tk.TclError:
                pass

        def bind_wheel(event=None):
            canvas.bind_all("<MouseWheel>", on_wheel)

        def unbind_wheel(event=None):
            try:
                canvas.unbind_all("<MouseWheel>")
            except tk.TclError:
                pass

        holder.bind("<Enter>", bind_wheel)
        holder.bind("<Leave>", unbind_wheel)
        holder.bind("<Destroy>", unbind_wheel)
        return inner

    def make_hero(self, parent, title, emoji, subtitle, buttons, avatar=None):
        
        HERO_H = 176
        HERO_A, HERO_B = "#7658BF", "#47308A"

        hero = tk.Canvas(parent, height=HERO_H, bg=self.theme.PURPLE, highlightthickness=0)
        hero.pack(fill="x")

        heading = hero.create_text(
            36, 52, text=title, anchor="w",
            font=("Arial", 27, "bold"), fill=self.theme.WHITE
        )
        hx = hero.bbox(heading)[2]
        hero.create_text(
            hx + 12, 52, text=emoji, anchor="w",
            font=("Segoe UI Emoji", 22), fill=self.theme.WHITE
        )
        hero.create_text(
            36, 92, text=subtitle, anchor="w",
            font=("Arial", 12, "bold"), fill="#E3DAF5"
        )

        date_text = hero.create_text(
            78, 135, text=datetime.now().strftime("%A, %B %d, %Y"), anchor="w",
            font=("Arial", 10, "bold"), fill="#EFE8FB"
        )
        dx1, dy1, dx2, dy2 = hero.bbox(date_text)
        pill = self._round_rect(
            hero, 36, dy1 - 6, dx2 + 16, dy2 + 6, 14,
            fill="#5C41A3", outline="#8B70CF"
        )
        hero.create_text(
            50, (dy1 + dy2) / 2, text="📅", anchor="w",
            font=("Segoe UI Emoji", 10), fill=self.theme.WHITE
        )
        hero.tag_lower(pill, date_text)

        has_right = bool(buttons)
        button_row = tk.Frame(hero, bg="#5B3FA2") if has_right else None
        sync = []   # kept for the gradient colour sync below

        for index, (text, command, primary) in enumerate(buttons):
            bg, fg, hover = (
                (self.theme.WHITE, "#503786", "#F0EBF9") if primary
                else ("#6A4DB3", self.theme.WHITE, "#7C5FC4")
            )
            button = tk.Button(
                button_row, text=text, command=command,
                font=("Arial", 11, "bold"), bg=bg, fg=fg,
                activebackground=hover, activeforeground=fg,
                bd=0, padx=22, pady=11, cursor="hand2"
            )
            button.bind("<Enter>", lambda e, b=button, h=hover: b.config(bg=h))
            button.bind("<Leave>", lambda e, b=button, c=bg: b.config(bg=c))
            button.pack(side="left", padx=(0 if index == 0 else 12, 0))

        window = (
            hero.create_window(0, HERO_H // 2, window=button_row, anchor="e")
            if has_right else None
        )

        def draw_profile(width):
            """Name + round picture drawn directly on the banner."""
            hero.delete("avatar")

            size = 84
            cx = width - 36 - size // 2
            cy = HERO_H // 2
            ring = hero.create_oval(
                cx - size // 2 + 3, cy - size // 2 + 3,
                cx + size // 2 - 3, cy + size // 2 - 3,
                fill="#6A4DB3", outline="#CDBDF2", width=3,
                tags=("avatar", "avatar_ring")
            )

            photo = (
                self.avatar_image(avatar.get("path", ""), size - 10)
                if avatar.get("path") else None
            )

            if photo:
                hero.avatar_photo = photo
                hero.create_image(cx, cy, image=photo, tags="avatar")
            else:
                hero.create_text(
                    cx, cy, text=avatar["initials"], fill=self.theme.WHITE,
                    font=("Arial", 24, "bold"), tags="avatar"
                )

            text_x = cx - size // 2 - 14
            hero.create_text(
                text_x, cy - 12, text=avatar["name"], anchor="e", fill=self.theme.WHITE,
                font=("Arial", 13, "bold"), tags="avatar"
            )
            hero.create_text(
                text_x, cy + 12, text="My Profile  →", anchor="e",
                fill="#E3DAF5", font=("Arial", 10, "bold"), tags="avatar"
            )

            hero.tag_raise("avatar")

        def hover_profile(on):
            hero.config(cursor="hand2" if on else "")
            hero.itemconfigure(
                "avatar_ring", outline=self.theme.WHITE if on else "#CDBDF2"
            )

        if avatar:
            hero.tag_bind("avatar", "<Enter>", lambda e: hover_profile(True))
            hero.tag_bind("avatar", "<Leave>", lambda e: hover_profile(False))
            hero.tag_bind("avatar", "<Button-1>", lambda e: avatar["command"]())

        def draw(event=None):
            width = max(hero.winfo_width(), 400)
            hero.delete("deco")

            strips = 56
            for i in range(strips):
                x1 = int(width * i / strips)
                x2 = int(width * (i + 1) / strips) + 1
                hero.create_rectangle(
                    x1, 0, x2, HERO_H, outline="",
                    fill=self._mix(HERO_A, HERO_B, i / (strips - 1)), tags="deco"
                )

            def base_at(x):
                return self._mix(HERO_A, HERO_B, min(max(x / width, 0), 1))

            for cx, cy, r, strength in (
                (width - 120, 10, 150, 0.07),
                (width - 330, HERO_H + 20, 95, 0.06),
                (width - 30, HERO_H - 5, 60, 0.09),
                (width * 0.52, -40, 70, 0.04),
            ):
                hero.create_oval(
                    cx - r, cy - r, cx + r, cy + r, outline="",
                    fill=self._mix(base_at(cx), self.theme.WHITE, strength), tags="deco"
                )

            hero.tag_lower("deco")
            if window is not None:
                hero.coords(window, width - 36, HERO_H // 2)
                color = base_at(width - 150)
                button_row.config(bg=color)

                for widget in sync:
                    widget.config(bg=color)

            if avatar:
                draw_profile(width)

        hero.bind("<Configure>", draw)
        draw()
        return hero

    def build_stat_cards(self, parent, items):
        
        row = tk.Frame(parent, bg=self.theme.BG)
        row.pack(fill="x", pady=(0, 22))

        count = len(items)

        for column in range(count):
            row.columnconfigure(column, weight=1, uniform="stat")

        for column, (label, icon, icon_bg, accent, value, note, tag) in enumerate(items):
            outer = tk.Frame(
                row, bg=self.theme.SURFACE, highlightbackground=self.theme.BORDER, highlightthickness=1
            )
            outer.grid(
                row=0, column=column, sticky="nsew",
                padx=(0, 14) if column < count - 1 else (0, 0)
            )

            tk.Frame(outer, bg=accent, height=3).pack(side="bottom", fill="x")

            box = tk.Frame(outer, bg=self.theme.SURFACE, padx=20, pady=16)
            box.pack(fill="both", expand=True)

            top = tk.Frame(box, bg=self.theme.SURFACE)
            top.pack(fill="x")

            tk.Label(
                top, text=label, font=("Arial", 9, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
            ).pack(side="left")

            tk.Label(
                top, text=icon, font=("Segoe UI Emoji", 14),
                bg=icon_bg, fg=self.theme.DARK_PURPLE, width=3
            ).pack(side="right", ipady=3)

            tk.Label(
                box, text=value, font=("Arial", 24, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w"
            ).pack(anchor="w", pady=(6, 2))

            bottom = tk.Frame(box, bg=self.theme.SURFACE)
            bottom.pack(fill="x")

            tk.Label(
                bottom, text=note, font=("Arial", 9),
                bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
            ).pack(side="left")

            if tag:
                tag_text, tag_bg, tag_fg = tag
                tk.Label(
                    bottom, text=tag_text, font=("Arial", 8, "bold"),
                    bg=tag_bg, fg=tag_fg, padx=8, pady=2
                ).pack(side="right")

    def build_action_cards(self, parent, actions, per_row=None):
        
        tk.Label(
            parent, text="⚡  Quick Actions",
            font=("Arial", 14, "bold"), bg=self.theme.BG, fg=self.theme.TEXT, anchor="w"
        ).pack(anchor="w", pady=(0, 12))

        grid = tk.Frame(parent, bg=self.theme.BG)
        grid.pack(fill="x", pady=(0, 22))

        count = len(actions)
        per_row = per_row or count
        last_row = (count - 1) // per_row

        for column in range(per_row):
            grid.columnconfigure(column, weight=1, uniform="act")

        wrap = 190 if per_row >= 4 else 260

        def inside(widget, x, y):
            found = widget.winfo_containing(x, y)

            while found is not None:
                if found is widget:
                    return True
                found = found.master

            return False

        for index, (icon, icon_bg, tag, tag_bg, tag_fg, title, description,
                    link, accent, command) in enumerate(actions):
            grid_row, column = divmod(index, per_row)

            card = tk.Frame(
                grid, bg=self.theme.SURFACE, padx=20, pady=18,
                highlightbackground=self.theme.BORDER, highlightthickness=1,
                cursor="hand2"
            )
            card.grid(
                row=grid_row, column=column, sticky="nsew",
                padx=(0, 14) if column < per_row - 1 else (0, 0),
                pady=(0, 14) if grid_row < last_row else (0, 0)
            )

            top = tk.Frame(card, bg=self.theme.SURFACE, cursor="hand2")
            top.pack(fill="x")

            icon_label = tk.Label(
                top, text=icon, font=("Segoe UI Emoji", 18),
                bg=icon_bg, fg=accent, width=3, cursor="hand2"
            )
            icon_label.pack(side="left", ipady=8)

            tag_label = tk.Label(
                top, text=tag, font=("Arial", 8, "bold"),
                bg=tag_bg, fg=tag_fg, padx=9, pady=2, cursor="hand2"
            )
            tag_label.pack(side="right", anchor="n")

            title_label = tk.Label(
                card, text=title, font=("Arial", 14, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w", cursor="hand2"
            )
            title_label.pack(anchor="w", pady=(14, 2))

            desc_label = tk.Label(
                card, text=description, font=("Arial", 9),
                bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w", justify="left",
                wraplength=wrap, cursor="hand2"
            )
            desc_label.pack(anchor="w", fill="x")

            tk.Frame(card, bg=self.theme.BORDER, height=1).pack(fill="x", pady=(12, 10))

            link_label = tk.Label(
                card, text=link, font=("Arial", 10, "bold"),
                bg=self.theme.SURFACE, fg=accent, anchor="w", cursor="hand2"
            )
            link_label.pack(anchor="w")

            parts = (
                card, top, icon_label, tag_label,
                title_label, desc_label, link_label
            )

            def on_enter(event, c=card, a=accent):
                c.config(highlightbackground=a)

            def on_leave(event, c=card):
                if not inside(c, event.x_root, event.y_root):
                    c.config(highlightbackground=self.theme.BORDER)

            for part in parts:
                part.bind("<Enter>", on_enter)
                part.bind("<Leave>", on_leave)
                part.bind("<Button-1>", lambda e, cmd=command: cmd())

    def build_notice(self, parent, icon, title, text, color, soft, meta=""):
        
        box = tk.Frame(
            parent, bg=soft, highlightbackground=color, highlightthickness=1
        )
        box.pack(fill="x", pady=(0, 18))

        tk.Frame(box, bg=color, width=6).pack(side="left", fill="y")

        inner = tk.Frame(box, bg=soft, padx=18, pady=14)
        inner.pack(side="left", fill="x", expand=True)

        head = tk.Frame(inner, bg=soft)
        head.pack(fill="x")

        tk.Label(
            head, text=f"{icon}  {title}", font=("Arial", 12, "bold"),
            bg=soft, fg=color, anchor="w"
        ).pack(side="left")

        if meta:
            tk.Label(
                head, text=meta, font=("Arial", 9), bg=soft, fg=self.theme.GRAY
            ).pack(side="right")

        message = tk.Label(
            inner, text=text, font=("Arial", 11), bg=soft, fg=self.theme.TEXT,
            anchor="w", justify="left", wraplength=800
        )
        message.pack(anchor="w", pady=(6, 0))

        box.bind(
            "<Configure>",
            lambda e: message.config(wraplength=max(e.width - 80, 200))
        )

    def build_banner(self, parent, text, link_text, command, color, soft):
        banner = tk.Frame(
            parent, bg=soft, padx=18, pady=12,
            highlightbackground=color, highlightthickness=1, cursor="hand2"
        )
        banner.pack(fill="x", pady=(0, 18))

        tk.Label(
            banner, text=text, font=("Arial", 12, "bold"),
            bg=soft, fg=color, cursor="hand2"
        ).pack(side="left")

        tk.Label(
            banner, text=link_text, font=("Arial", 10, "bold"),
            bg=soft, fg=self.theme.DARK_PURPLE, cursor="hand2"
        ).pack(side="right")

        for widget in (banner, *banner.winfo_children()):
            widget.bind("<Button-1>", lambda e: command())

    def make_textbox(self, parent, height=5, width=50):
        return tk.Text(
            parent, width=width, height=height, font=("Arial", 11),
            wrap="word", bg=self.theme.SURFACE, fg=self.theme.TEXT, insertbackground=self.theme.TEXT,
            relief="flat", highlightthickness=1,
            highlightbackground=self.theme.ENTRY_BORDER, highlightcolor=self.theme.PURPLE,
            padx=10, pady=8
        )

    def make_switch(self, parent, variable, on_text, off_text):
        row = tk.Frame(parent, bg=self.theme.SURFACE, cursor="hand2")

        canvas = tk.Canvas(
            row, width=54, height=30, bg=self.theme.SURFACE,
            highlightthickness=0, cursor="hand2"
        )
        canvas.pack(side="left")

        label = tk.Label(
            row, font=("Arial", 11, "bold"), bg=self.theme.SURFACE, cursor="hand2"
        )
        label.pack(side="left", padx=(12, 0))

        def draw(*args):
            try:
                on = variable.get()
                canvas.delete("all")
                self._round_rect(
                    canvas, 2, 3, 52, 27, 12,
                    fill=self.theme.RED if on else self.theme.ENTRY_BORDER, outline=""
                )
                x = 40 if on else 16
                canvas.create_oval(x - 10, 5, x + 10, 25, fill=self.theme.WHITE, outline="")
                label.config(
                    text=on_text if on else off_text, fg=self.theme.RED if on else self.theme.GRAY
                )
            except tk.TclError:
                pass

        def toggle(event=None):
            variable.set(not variable.get())

        for widget in (row, canvas, label):
            widget.bind("<Button-1>", toggle)

        variable.trace_add("write", draw)
        draw()
        return row