import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from backend.printing import PrintService
from backend.services import Services
from frontend.admin_screens import AdminScreens
from frontend.auth_screens import AuthScreens
from frontend.order_screens import OrderScreens
from frontend.student_screens import StudentScreens
from frontend.theme import Theme
from frontend.widgets import Widgets


class App:

    def __init__(self, services=None, printing=None):
        self.services = services or Services()
        self.printing = printing or PrintService()
        self.theme = Theme()

        
        self.current_user = ""      
        self.current_name = ""      
        self.current_role = ""
        self.content_frame = None

       
        self.printer_label = None
        self.printer_dot = None
        self.printer_job = None
        self.printer_state = {"name": "__unset__"}
        self.printer_result = {"ready": False, "data": None}

    
        self.order_actions = {"print": None}   
        self.nav = {"items": {}, "active": None, "badge": None}
        self.seen = {"announcement": None}     


        self.root = tk.Tk()
        self.root.title("SMCII Printing Service and Shop")
        self.root.geometry("1250x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg=self.theme.BG)

        self.style = ttk.Style()
        self.style.theme_use("clam")


        self.ui = Widgets(self)
        self.auth = AuthScreens(self)
        self.student = StudentScreens(self)
        self.admin = AdminScreens(self)
        self.order_screens = OrderScreens(self)

        self.apply_theme("light")

        self.root.bind("<Control-p>", self.on_ctrl_p)
        self.root.bind("<Control-P>", self.on_ctrl_p)
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_exit)

    def show_error(self, error):
        messagebox.showerror(error.title, error.message)

    def save_everything(self):
        for message in self.services.save_all():
            messagebox.showerror("File Error", message)

    def get_user_orders(self):
        return self.services.get_user_orders(self.current_role, self.current_user)

    def open_file(self, path):
        try:
            self.printing.open_file(path)
        except FileNotFoundError:
            messagebox.showerror(
                "File Not Found", "The stored file could not be found."
            )
        except OSError as error:
            messagebox.showerror("Open Failed", f"Could not open file.\n{error}")

    def print_file(self, path, copies=1):
        try:
            self.printing.print_file(path, copies)
            return True
        except FileNotFoundError:
            messagebox.showerror(
                "File Not Found", "The stored PDF could not be found."
            )
        except Exception as error:
            messagebox.showerror(
                "Print Failed", f"Could not print the file.\n{error}"
            )
        return False

    def apply_printer(self, info):
        previous = self.printer_state["name"]
        name = info["name"] if info else None

        try:
            if info:
                self.printer_dot.config(fg="#5FD38D")
                self.printer_label.config(text=f"{name}\nConnected", fg=self.theme.WHITE)
            else:
                self.printer_dot.config(fg="#E26D6D")
                self.printer_label.config(text="No printer\nconnected", fg="#C9BFDF")
        except tk.TclError:
            return

        if name == previous:
            return

        self.printer_state["name"] = name

        if name:
            self.ui.show_toast("🖨  Printer Connected", name, self.theme.GREEN)
        elif previous == "__unset__":
            self.ui.show_toast(
                "⚠  No Printer Detected",
                "Connect a printer to enable printing.", self.theme.ORANGE
            )
        else:
            self.ui.show_toast(
                "⚠  Printer Disconnected",
                f"{previous} is no longer available.", self.theme.RED
            )

    def printer_widget_alive(self):
        try:
            return self.printer_label is not None and bool(self.printer_label.winfo_exists())
        except tk.TclError:
            return False

    def printer_cycle(self):

        if not self.printer_widget_alive():
            return

        self.printer_result["ready"] = False

        def work():
            self.printer_result["data"] = self.printing.detect_printer()
            self.printer_result["ready"] = True

        threading.Thread(target=work, daemon=True).start()
        self.printer_job = self.root.after(400, self.printer_wait)

    def printer_wait(self):

        if not self.printer_widget_alive():
            return

        if self.printer_result["ready"]:
            self.apply_printer(self.printer_result["data"])
            self.printer_job = self.root.after(6000, self.printer_cycle)
        else:
            self.printer_job = self.root.after(300, self.printer_wait)

    def stop_printer_monitor(self):

        if self.printer_job:
            try:
                self.root.after_cancel(self.printer_job)
            except tk.TclError:
                pass

        self.printer_job = None
        self.printer_label = None
        self.printer_dot = None

    def apply_theme(self, mode):
        self.theme.apply(mode)

        self.root.configure(bg=self.theme.BG)

        self.style.configure(
            "Treeview",
            background=self.theme.SURFACE, foreground=self.theme.TEXT, fieldbackground=self.theme.SURFACE,
            rowheight=36, font=("Arial", 11), bordercolor=self.theme.BORDER
        )
        self.style.configure(
            "Treeview.Heading",
            background=self.theme.LIGHT_PURPLE, foreground=self.theme.DARK_PURPLE,
            font=("Arial", 10, "bold"), padding=10
        )
        self.style.map(
            "Treeview",
            background=[("selected", self.theme.SELECT)],
            foreground=[("selected", self.theme.TEXT)]
        )
        self.style.configure(
            "TCombobox",
            padding=7, font=("Arial", 11),
            fieldbackground=self.theme.SURFACE, background=self.theme.SURFACE,
            foreground=self.theme.TEXT, arrowcolor=self.theme.TEXT, bordercolor=self.theme.ENTRY_BORDER
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", self.theme.SURFACE)],
            foreground=[("readonly", self.theme.TEXT)],
            selectbackground=[("readonly", self.theme.SURFACE)],
            selectforeground=[("readonly", self.theme.TEXT)]
        )
        self.style.configure(
            "Vertical.TScrollbar",
            background=self.theme.BORDER, troughcolor=self.theme.BG, bordercolor=self.theme.BG, arrowcolor=self.theme.TEXT
        )

        self.root.option_add("*TCombobox*Listbox.background", self.theme.SURFACE)
        self.root.option_add("*TCombobox*Listbox.foreground", self.theme.TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.theme.SELECT)
        self.root.option_add("*TCombobox*Listbox.selectForeground", self.theme.TEXT)

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def refresh_nav(self, name=None):
        if name:
            self.nav["page"] = name
            self.nav["active"] = name if name in self.nav["items"] else None

        for key, (widgets, set_color) in self.nav["items"].items():
            try:
                set_color(self.theme.PURPLE if key == self.nav["active"] else self.theme.SIDEBAR_BG)
            except tk.TclError:
                pass

        try:
            if self.nav["badge"] is not None:
                self.nav["badge"].config(
                    text=str(sum(item["quantity"] for item in self.services.cart))
                )
        except tk.TclError:
            pass

    def clear_content(self):
        self.order_actions["print"] = None

        for widget in self.content_frame.winfo_children():
            widget.destroy()

       
        self.content_frame.config(padx=35, pady=30)
        self.refresh_nav(sys._getframe(1).f_code.co_name)

    def on_ctrl_p(self, event=None):
        """Ctrl + P: admin prints the selected PDF order(s) in Order History."""
        handler = self.order_actions.get("print")

        if self.current_role == "Admin" and handler:
            handler()

        return "break"

    def confirm_exit(self):
        if messagebox.askyesno(
            "Exit Application",
            "Are you sure you want to exit?\n\n"
            "Any items in your shopping cart that were not checked out will be lost."
        ):

            self.save_everything()
            self.root.destroy()

    def return_main_menu(self):
        if self.current_role == "Admin":
            self.admin.main_menu()
        else:
            self.student.student_home()

    def open_system(self, rebuild=False):

        self.apply_theme(self.services.get_theme())

        self.stop_printer_monitor()

        if not rebuild:
            self.printer_state["name"] = "__unset__"
            self.seen["announcement"] = None

        self.clear_root()
        self.root.configure(bg=self.theme.BG)

        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        sidebar = tk.Frame(self.root, bg=self.theme.SIDEBAR_BG, width=235)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        printer_box = tk.Frame(sidebar, bg="#362C4D", padx=14, pady=10)
        printer_box.pack(side="bottom", fill="x", padx=14, pady=16)

        tk.Label(
            printer_box, text="PRINTER", font=("Arial", 8, "bold"),
            bg="#362C4D", fg="#C9BFDF"
        ).pack(anchor="w")

        printer_row = tk.Frame(printer_box, bg="#362C4D")
        printer_row.pack(anchor="w", fill="x", pady=(4, 0))

        self.printer_dot = tk.Label(
            printer_row, text="●", font=("Arial", 12),
            bg="#362C4D", fg="#E5C26B"
        )
        self.printer_dot.pack(side="left", anchor="n")

        self.printer_label = tk.Label(
            printer_row, text="Checking...\n", font=("Arial", 10, "bold"),
            bg="#362C4D", fg=self.theme.WHITE, justify="left", anchor="w",
            wraplength=150
        )
        self.printer_label.pack(side="left", padx=(6, 0))

        tk.Label(
            sidebar,
            text="PRINTING\nSERVICE",
            font=("Arial", 20, "bold"),
            bg=self.theme.SIDEBAR_BG,
            fg=self.theme.WHITE,
            justify="left"
        ).pack(anchor="w", padx=25, pady=(35, 5))

        tk.Label(
            sidebar,
            text=f"{self.current_role.upper()} ACCOUNT",
            font=("Arial", 10, "bold"),
            bg=self.theme.SIDEBAR_BG,
            fg="#C9BFDF"
        ).pack(anchor="w", padx=25, pady=(0, 30))

        if self.current_role == "Admin":
            tk.Label(
                sidebar,
                text=f"Logged in: {self.current_name}",
                font=("Arial", 10),
                bg=self.theme.SIDEBAR_BG,
                fg=self.theme.WHITE,
                justify="left",
                wraplength=190
            ).pack(anchor="w", padx=25, pady=(0, 25))
        else:
            tk.Frame(sidebar, bg="#3A2F55", height=1).pack(
                fill="x", padx=20, pady=(0, 14)
            )

            profile = tk.Frame(sidebar, bg=self.theme.SIDEBAR_BG, cursor="hand2")
            profile.pack(fill="x", padx=22, pady=(0, 14))

            avatar = tk.Canvas(
                profile, width=46, height=46, bg=self.theme.SIDEBAR_BG,
                highlightthickness=0, cursor="hand2"
            )
            self.ui.draw_avatar(
                avatar, 46, self.services.profile_picture(self.current_user),
                self.ui.student_initials(), "#A98BE6", self.theme.PURPLE, 11
            )
            avatar.pack(side="left")

            who = tk.Frame(profile, bg=self.theme.SIDEBAR_BG, cursor="hand2")
            who.pack(side="left", padx=(10, 0))

            tk.Label(
                who, text=self.current_name, font=("Arial", 11, "bold"),
                bg=self.theme.SIDEBAR_BG, fg=self.theme.WHITE, anchor="w", wraplength=140,
                justify="left", cursor="hand2"
            ).pack(anchor="w")

            tk.Label(
                who, text=f"ID: {self.current_user}", font=("Arial", 9),
                bg=self.theme.SIDEBAR_BG, fg="#C9BFDF", anchor="w", cursor="hand2"
            ).pack(anchor="w")

            for widget in (profile, avatar, who, *who.winfo_children()):
                widget.bind("<Button-1>", lambda e: self.student.profile_page())

            tk.Frame(sidebar, bg="#3A2F55", height=1).pack(
                fill="x", padx=20, pady=(0, 14)
            )

        self.nav["items"] = {}
        self.nav["active"] = None
        self.nav["badge"] = None

        def nav_button(icon, text, command, badge=False):
            row = tk.Frame(sidebar, bg=self.theme.SIDEBAR_BG, cursor="hand2")
            row.pack(fill="x", padx=8, pady=3)

            icon_label = tk.Label(
                row,
                text=icon,
                font=("Segoe UI Emoji", 13),
                width=3,
                bg=self.theme.SIDEBAR_BG,
                fg=self.theme.WHITE,
                anchor="center",
                cursor="hand2"
            )
            icon_label.pack(side="left", padx=(17, 0), pady=12)

            text_label = tk.Label(
                row,
                text=text,
                font=("Arial", 11),
                bg=self.theme.SIDEBAR_BG,
                fg=self.theme.WHITE,
                anchor="w",
                cursor="hand2"
            )
            text_label.pack(side="left", fill="x", expand=True, padx=(6, 0))

            widgets = (row, icon_label, text_label)
            key = command.__name__

            def set_color(color):
                for widget in widgets:
                    widget.config(bg=color)

            if badge:
                badge_label = tk.Label(
                    row, text="0", font=("Arial", 9, "bold"),
                    bg="#4B3A78", fg=self.theme.WHITE, padx=7, pady=1, cursor="hand2"
                )
                badge_label.pack(side="right", padx=(0, 14))
                self.nav["badge"] = badge_label
                widgets = widgets + (badge_label,)

                def set_color(color, base=widgets[:3]):
                    for widget in base:
                        widget.config(bg=color)

            if command not in (self.logout, self.confirm_exit):
                self.nav["items"][key] = (widgets, set_color)

            def hover_in(e):
                if self.nav["active"] != key:
                    set_color("#3A2F55")

            def hover_out(e):
                set_color(self.theme.PURPLE if self.nav["active"] == key else self.theme.SIDEBAR_BG)

            for widget in widgets:
                widget.bind("<Enter>", hover_in)
                widget.bind("<Leave>", hover_out)
                widget.bind("<Button-1>", lambda e: command())

        self.content_frame = tk.Frame(
            self.root,
            bg=self.theme.BG,
            padx=35,
            pady=30
        )
        self.content_frame.pack(side="right", fill="both", expand=True)

        if self.current_role == "Admin":
            # Admin only manages the shop and reviews orders
            nav_button("📊", "Dashboard", self.admin.main_menu)
            nav_button("➕", "Add Shop Item", self.admin.admin_add_item_page)
            nav_button("📋", "Order History", self.order_screens.view_orders_page)
            nav_button("📢", "Notices", self.admin.admin_notices_page)

        else:
            nav_button("🏠", "Student Home", self.student.student_home)
            nav_button("🖨", "Place a Print Order", self.student.printing_page)
            nav_button("🛍", "Buy School Supplies", self.student.shop_page)
            nav_button("🛒", "Shopping Cart", self.student.cart_page, badge=True)
            nav_button("📋", "My Order History", self.order_screens.view_orders_page)

        tk.Frame(
            sidebar,
            bg="#4A405B",
            height=1
        ).pack(fill="x", padx=20, pady=20)

        nav_button(
            "☀" if self.theme.mode == "dark" else "🌙",
            "Light Mode" if self.theme.mode == "dark" else "Dark Mode",
            self.toggle_theme
        )
        nav_button("🚪", "Log Out", self.logout)
        nav_button("❌", "Exit Application", self.confirm_exit)

        if self.current_role == "Admin":
            self.admin.main_menu()
        else:
            self.student.student_home()

        self.printer_cycle()

        if self.current_role == "Student" and not rebuild:
            ready = self.services.ready_orders(self.current_user)

            if ready:
                lines = "\n".join(
                f"• {self.services.order_details_text(o)}" for o in ready[:5]
                )
                self.root.after(500, lambda: messagebox.showinfo(
                    "Order Ready for Pickup",
                    f"{len(ready)} of your order(s) can be picked up now:\n\n"
                    f"{lines}"
                ))

    def toggle_theme(self):
        previous = self.nav.get("page")
        mode = "light" if self.theme.mode == "dark" else "dark"

        self.services.set_theme(mode)
        self.apply_theme(mode)
        self.open_system(rebuild=True)

        page = self.find_page(previous)

        if previous not in (None, "student_home", "main_menu") and callable(page):
            page()

    def logout(self):

        if messagebox.askyesno(
            "Log Out",
            "Are you sure you want to log out?"
        ):
            # save everything before leaving the session
            self.save_everything()

            self.stop_printer_monitor()
            self.current_user = ""
            self.current_name = ""
            self.current_role = ""
            self.services.cart.clear()
            self.order_actions["print"] = None
            self.auth.login_page()

    def run(self):
        for warning in self.services.init():
            messagebox.showwarning("File Error", warning)

        self.auth.login_page()
        self.root.mainloop()

    def find_page(self, name):
        for group in (self.student, self.admin, self.order_screens):
            page = getattr(group, name, None)

            if callable(page):
                return page

        return None


def run():
    App().run()


if __name__ == "__main__":
    run()