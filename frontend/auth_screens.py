import os
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

from backend.services import ServiceError
from frontend.screen import Screen


class AuthScreens(Screen):

    PANEL_SOFT = "#F4EFF8"
    ASSETS_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets"
    )

    def build_auth_shell(self):
        self.app.apply_theme("light")   # login / register screens are always light
        """Soft gradient on the left with a floating card, picture on the right.

        Returns the card frame that the page puts its form into."""
        self.app.clear_root()
        self.root.configure(bg=self.theme.SURFACE)

        left = tk.Frame(self.root, bg="#FCF8FB", width=560)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        bg_label = tk.Label(left, bd=0, bg="#FCF8FB")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        soft = self.ui.make_soft_background()

        def resize_background(event=None):
            width, height = left.winfo_width(), left.winfo_height()

            if width < 2 or height < 2:
                return

            left.bg_photo = ImageTk.PhotoImage(
                soft.resize((width, height), Image.Resampling.BICUBIC)
            )
            bg_label.config(image=left.bg_photo)

        left.bind("<Configure>", resize_background)


        right = tk.Frame(self.root, bg=self.PANEL_SOFT)
        right.pack(side="right", fill="both", expand=True)

        image_label = tk.Label(right, bg=self.PANEL_SOFT, bd=0)
        image_label.place(x=22, y=22, relwidth=1, relheight=1, width=-44, height=-44)

        try:
            original_image = Image.open(os.path.join(self.ASSETS_DIR, "smc.jpg")).convert("RGB")

            def resize_image(event=None):
                width = right.winfo_width() - 44
                height = right.winfo_height() - 44

                if width < 2 or height < 2:
                    return

                right.photo = self.ui.rounded_photo(
                    original_image, (width, height), 28, (244, 239, 248)
                )
                image_label.config(image=right.photo)

            right.bind("<Configure>", resize_image)

        except (FileNotFoundError, OSError):
            tk.Label(
                right,
                text="SMCII PRINTING SERVICE\nAND SHOP",
                font=("Arial", 28, "bold"),
                bg=self.PANEL_SOFT,
                fg=self.theme.DARK_PURPLE,
                justify="center"
            ).place(relx=0.5, rely=0.5, anchor="center")

        tagline = tk.Frame(
            right, bg=self.theme.SURFACE, padx=24, pady=14,
            highlightbackground=self.theme.BORDER, highlightthickness=1
        )
        tagline.place(relx=0.06, rely=0.92, anchor="sw")

        tk.Label(
            tagline, text="Print. Shop. Done.", font=("Arial", 16, "bold"),
            bg=self.theme.SURFACE, fg=self.theme.DARK_PURPLE
        ).pack(anchor="w")

        tk.Label(
            tagline, text="Fast school printing and supplies at SMCII",
            font=("Arial", 10), bg=self.theme.SURFACE, fg=self.theme.GRAY
        ).pack(anchor="w", pady=(2, 0))

        card = tk.Frame(
            left, bg=self.theme.SURFACE, padx=36, pady=32,
            highlightbackground="#E8E3F0", highlightthickness=1
        )
        card.place(relx=0.5, rely=0.5, anchor="center", width=440)
        return card

    def brand_header(self, form, compact=False):
        if not compact:
            badge_row = tk.Frame(form, bg=self.theme.SURFACE)
            badge_row.pack(anchor="w", pady=(0, 14))

            badge = tk.Canvas(
                badge_row,
                width=68,
                height=68,
                bg=self.theme.SURFACE,
                highlightthickness=0
            )
            badge.pack(side="left")
            badge.create_oval(2, 2, 66, 66, fill=self.theme.LIGHT_PURPLE, outline="")
            badge.create_oval(9, 9, 59, 59, fill=self.theme.PURPLE, outline="")
            badge.create_text(
                34, 34,
                text="🖨",
                font=("Segoe UI Emoji", 22),
                fill=self.theme.WHITE
            )

            for small_icon in ("📄", "✏", "📚"):
                tk.Label(
                    badge_row,
                    text=small_icon,
                    font=("Segoe UI Emoji", 14),
                    width=2,
                    bg=self.theme.LIGHT_PURPLE,
                    fg=self.theme.DARK_PURPLE
                ).pack(side="left", padx=(10, 0), ipady=6)

        tk.Frame(
            form,
            bg=self.theme.PURPLE,
            width=60,
            height=4
        ).pack(anchor="w", pady=(0, 10 if compact else 14))

        tk.Label(
            form,
            text="SMCII PRINTING SERVICE",
            font=("Arial", 18 if compact else 20, "bold"),
            bg=self.theme.SURFACE,
            fg=self.theme.DARK_PURPLE
        ).pack(anchor="w", pady=(0, 3))

        tk.Label(
            form,
            text="AND SHOP",
            font=("Arial", 13 if compact else 15),
            bg=self.theme.SURFACE,
            fg=self.theme.GRAY
        ).pack(anchor="w", pady=(0, 14 if compact else 18))

    def login_page(self):
        form = self.build_auth_shell()

        tk.Label(
            form, text="🖨  SMCII PRINTING SERVICE AND SHOP",
            font=("Arial", 9, "bold"), bg=self.theme.SURFACE, fg=self.theme.PURPLE
        ).pack(anchor="w", pady=(0, 14))

        tk.Label(
            form, text="Welcome back", font=("Arial", 24, "bold"),
            bg=self.theme.SURFACE, fg=self.theme.TEXT
        ).pack(anchor="w")

        self.ui.make_label(
            form, "Log in to continue to your account.", 10, False, self.theme.GRAY
        ).pack(anchor="w", pady=(2, 18))

        self.ui.make_label(form, "Login As", 10, True).pack(anchor="w", pady=(0, 5))

        role_box = ttk.Combobox(
            form,
            values=["Admin", "Student"],
            state="readonly",
            font=("Arial", 12)
        )
        role_box.current(0)
        role_box.pack(fill="x", ipady=4, pady=(0, 14))

        fields = tk.Frame(form, bg=self.theme.SURFACE)
        fields.pack(fill="x")

        user_label = self.ui.make_label(fields, "Username", 10, True)   
        user_label.pack(anchor="w", pady=(0, 5))

        username_box, username_entry = self.ui.make_round_field(fields)
        username_box.pack(fill="x", pady=(0, 14))

        self.ui.make_label(fields, "Password", 10, True).pack(anchor="w", pady=(0, 5))

        password_box, password_entry = self.ui.make_round_field(fields, password=True)
        password_box.pack(fill="x", pady=(0, 12))

        
        option_row = tk.Frame(fields, bg=self.theme.SURFACE)
        option_row.pack(fill="x", pady=(0, 18))

        remember_var = tk.BooleanVar(value=False)

        self.ui.make_check(option_row, "Remember me", remember_var).pack(side="left")

        forgot_link = tk.Label(
            option_row, text="Forgot Password?",
            font=("Arial", 9, "bold"), bg=self.theme.SURFACE, fg=self.theme.TEXT, cursor="hand2"
        )
        forgot_link.bind("<Button-1>", lambda e: self.forgot_password_page())

        def do_login():

            username = username_entry.get().strip()
            password = password_entry.get()

            if role_box.get() == "Admin":
                if self.services.login_admin(username, password):
                    self.app.current_user = username
                    self.app.current_name = "Admin"
                    self.app.current_role = "Admin"

                    self.services.set_remembered("Admin", username, remember_var.get())

                    messagebox.showinfo("Login Successful", "Welcome, Admin!")
                    self.app.open_system()
                else:
                    messagebox.showerror(
                        "Login Failed",
                        "Incorrect admin username or password."
                    )
                return

            info = self.services.login_student(username, password)

            if not info:
                messagebox.showerror(
                    "Login Failed",
                    "Incorrect ID number or password.\n"
                    "No account yet? Click \"Register here\"."
                )
                return

            self.app.current_user = username
            self.app.current_name = f"{info['first']} {info['last']}"
            self.app.current_role = "Student"

            self.services.set_remembered("Student", username, remember_var.get())

            messagebox.showinfo(
                "Login Successful",
                f"Welcome, {info['first']}!"
            )
            self.app.open_system()

        login_button = self.ui.make_button(
            form, "Sign in", do_login, width=30, color="#17121F"
        )
        login_button.pack(fill="x", pady=(0, 16))

        extra = tk.Frame(form, bg=self.theme.SURFACE)
        extra.pack(fill="x")

        register_row = tk.Frame(extra, bg=self.theme.SURFACE)

        tk.Label(
            register_row, text="New student?", font=("Arial", 10),
            bg=self.theme.SURFACE, fg=self.theme.GRAY
        ).pack(side="left")

        register_link = tk.Label(
            register_row, text=" Register here",
            font=("Arial", 10, "bold"),
            bg=self.theme.SURFACE, fg=self.theme.TEXT, cursor="hand2"
        )
        register_link.pack(side="left")
        register_link.bind("<Button-1>", lambda e: self.register_page())

        def change_role(event=None):
            username_entry.delete(0, tk.END)
            password_entry.delete(0, tk.END)

            if role_box.get() == "Student":
                user_label.config(text="ID Number")
                register_row.pack(anchor="center")
                forgot_link.pack(side="right")
            else:
                user_label.config(text="Username")
                register_row.pack_forget()
                forgot_link.pack_forget()

            username_entry.focus_set()

        role_box.bind("<<ComboboxSelected>>", change_role)

        password_entry.bind("<Return>", lambda event: do_login())
        username_entry.bind("<Return>", lambda event: password_entry.focus_set())

        username_entry.focus_set()

        saved = self.services.get_remembered()

        if saved:
            role_box.set(saved[0])
            change_role()
            username_entry.insert(0, saved[1])
            remember_var.set(True)
            password_entry.focus_set()

    def register_page(self):
        form = self.build_auth_shell()
        self.brand_header(form, compact=True)

        self.ui.make_label(form, "Create Student Account", 14, True, self.theme.DARK_PURPLE).pack(
            anchor="w", pady=(0, 10)
        )

        name_row = tk.Frame(form, bg=self.theme.SURFACE)
        name_row.pack(fill="x")
        name_row.columnconfigure(0, weight=1, uniform="n")
        name_row.columnconfigure(1, weight=1, uniform="n")

        first_box = tk.Frame(name_row, bg=self.theme.SURFACE)
        first_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.ui.make_label(first_box, "First Name", 10, True).pack(anchor="w", pady=(0, 4))
        first_entry = self.ui.make_entry(first_box, width=12)
        first_entry.pack(fill="x", ipady=7, pady=(0, 10))

        last_box = tk.Frame(name_row, bg=self.theme.SURFACE)
        last_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.ui.make_label(last_box, "Last Name", 10, True).pack(anchor="w", pady=(0, 4))
        last_entry = self.ui.make_entry(last_box, width=12)
        last_entry.pack(fill="x", ipady=7, pady=(0, 10))

        self.ui.make_label(form, "ID Number", 10, True).pack(anchor="w", pady=(0, 4))
        id_entry = self.ui.make_entry(form, width=32)
        id_entry.pack(fill="x", ipady=7, pady=(0, 10))

        self.ui.make_label(form, "Password", 10, True).pack(anchor="w", pady=(0, 4))
        password_box, password_entry = self.ui.make_password_field(form, 7)
        password_box.pack(fill="x", pady=(0, 10))

        self.ui.make_label(form, "Confirm Password", 10, True).pack(anchor="w", pady=(0, 4))
        confirm_box, confirm_entry = self.ui.make_password_field(form, 7)
        confirm_box.pack(fill="x", pady=(0, 16))

        def submit_registration():
            first = first_entry.get().strip()
            last = last_entry.get().strip()

            try:
                self.services.register_student(
                    first, last, id_entry.get(),
                    password_entry.get(), confirm_entry.get()
                )
            except ServiceError as error:
                self.app.show_error(error)
                return

            messagebox.showinfo(
                "Registration Successful",
                f"Account created for {first} {last}.\n"
                "You can now log in with your ID number and password."
            )
            self.login_page()

        self.ui.make_button(
            form, "REGISTER", submit_registration, width=30
        ).pack(fill="x", pady=(0, 10))

        back = tk.Label(
            form, text="← Back to login",
            font=("Arial", 10, "bold"), bg=self.theme.SURFACE, fg=self.theme.PURPLE, cursor="hand2"
        )
        back.pack(anchor="w")
        back.bind("<Button-1>", lambda e: self.login_page())

        confirm_entry.bind("<Return>", lambda e: submit_registration())
        first_entry.focus_set()

    def forgot_password_page(self):
        form = self.build_auth_shell()
        self.brand_header(form, compact=True)

        self.ui.make_label(form, "Reset Password", 14, True, self.theme.DARK_PURPLE).pack(
            anchor="w", pady=(0, 2)
        )
        self.ui.make_label(
            form, "Enter your registered details to verify it's you.",
            9, False, self.theme.GRAY
        ).pack(anchor="w", pady=(0, 10))

        name_row = tk.Frame(form, bg=self.theme.SURFACE)
        name_row.pack(fill="x")
        name_row.columnconfigure(0, weight=1, uniform="n")
        name_row.columnconfigure(1, weight=1, uniform="n")

        first_box = tk.Frame(name_row, bg=self.theme.SURFACE)
        first_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.ui.make_label(first_box, "First Name", 10, True).pack(anchor="w", pady=(0, 4))
        first_entry = self.ui.make_entry(first_box, width=12)
        first_entry.pack(fill="x", ipady=7, pady=(0, 10))

        last_box = tk.Frame(name_row, bg=self.theme.SURFACE)
        last_box.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self.ui.make_label(last_box, "Last Name", 10, True).pack(anchor="w", pady=(0, 4))
        last_entry = self.ui.make_entry(last_box, width=12)
        last_entry.pack(fill="x", ipady=7, pady=(0, 10))

        self.ui.make_label(form, "ID Number", 10, True).pack(anchor="w", pady=(0, 4))
        id_entry = self.ui.make_entry(form, width=32)
        id_entry.pack(fill="x", ipady=7, pady=(0, 10))

        self.ui.make_label(form, "New Password", 10, True).pack(anchor="w", pady=(0, 4))
        password_box, password_entry = self.ui.make_password_field(form, 7)
        password_box.pack(fill="x", pady=(0, 10))

        self.ui.make_label(form, "Confirm New Password", 10, True).pack(
            anchor="w", pady=(0, 4)
        )
        confirm_box, confirm_entry = self.ui.make_password_field(form, 7)
        confirm_box.pack(fill="x", pady=(0, 16))

        def submit_reset():
            try:
                self.services.reset_password(
                    first_entry.get(), last_entry.get(), id_entry.get(),
                    password_entry.get(), confirm_entry.get()
                )
            except ServiceError as error:
                self.app.show_error(error)
                return

            messagebox.showinfo(
                "Password Reset",
                "Your password was changed.\nYou can now log in."
            )
            self.login_page()

        self.ui.make_button(
            form, "RESET PASSWORD", submit_reset, width=30
        ).pack(fill="x", pady=(0, 10))

        back = tk.Label(
            form, text="← Back to login",
            font=("Arial", 10, "bold"), bg=self.theme.SURFACE, fg=self.theme.PURPLE, cursor="hand2"
        )
        back.pack(anchor="w")
        back.bind("<Button-1>", lambda e: self.login_page())

        confirm_entry.bind("<Return>", lambda e: submit_reset())
        first_entry.focus_set()