"""FRONTEND - admin pages: dashboard, shop items and notices."""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from PIL import Image

from backend.services import ServiceError
from frontend.screen import Screen


class AdminScreens(Screen):
    """Everything the admin can do."""

    def clear_dashboard_stats(self):
        if not messagebox.askyesno(
            "Clear Today's Stats",
            "Reset Total Orders, Print Orders, Shop Orders and Total Sales "
            "back to zero?\n\n"
            "Your Order History will NOT be deleted."
        ):
            return

        try:
            self.services.clear_stats()
            messagebox.showinfo(
                "Stats Cleared",
                "The dashboard counters were reset to zero."
            )
        except ServiceError as error:
            self.app.show_error(error)

        self.main_menu()

    def main_menu(self):
        if self.app.current_role != "Admin":
            self.app.student.student_home()
            return

        self.app.clear_content()
        self.app.content_frame.config(padx=0, pady=0)   # hero sits flush like the design

        counted = self.services.counted_orders()
        total_orders = len(counted)
        printing_orders = sum(
            1 for o in counted if o["type"] == "Printing Service"
        )
        shop_orders = sum(1 for o in counted if o["type"] == "Shop Order")
        total_sales = sum(o["total"] for o in counted)
        waiting = [
            o for o in self.services.orders
            if o.get("status", "Pending") in ("Pending", "Printing")
        ]

        page = self.ui.make_scroll_page(self.app.content_frame)

        self.ui.make_hero(
            page, "Admin Dashboard", "📊",
            "Manage shop items and review printing and shop orders.",
            []
        )

        body = tk.Frame(page, bg=self.theme.BG, padx=35)
        body.pack(fill="both", expand=True, pady=(22, 0))

        if self.services.get_maintenance()["on"]:
            self.ui.build_banner(
                body, "🛠  Maintenance mode is ON: students can't place print orders",
                "Manage  →", self.admin_notices_page, self.theme.RED, self.theme.TINT_RED
            )

        if waiting:
            self.ui.build_banner(
                body, f"⏳  {len(waiting)} order(s) waiting to be processed",
                "Open Order History  →", self.app.order_screens.view_orders_page, self.theme.ORANGE, self.theme.TINT_ORANGE
            )

        since_text = (
            f"Since {self.services.stats['since']}" if self.services.stats["since"] else "All orders"
        )

        self.ui.build_stat_cards(body, [
            ("TOTAL ORDERS", "📦", self.theme.LIGHT_PURPLE, self.theme.PURPLE, str(total_orders),
             since_text, None),
            ("PRINT ORDERS", "🖨", self.theme.TINT_BLUE, self.theme.BLUE, str(printing_orders),
             "PDF jobs from students", None),
            ("SHOP ORDERS", "🛍", self.theme.TINT_ORANGE, self.theme.ORANGE, str(shop_orders),
             "School supplies sold", None),
            ("TOTAL SALES", "💰", self.theme.TINT_GREEN, self.theme.GREEN, self.ui.money(total_sales),
             "Revenue counted", ("Sales", self.theme.TINT_GREEN, self.theme.GREEN)),
        ])

        self.ui.build_action_cards(body, [
            ("➕", self.theme.LIGHT_PURPLE, "Shop", self.theme.TINT_PURPLE, self.theme.PURPLE,
             "Add Shop Item",
             "Add, edit or remove school supplies, prices and pictures.",
             "Manage Items  →", self.theme.PURPLE, self.admin_add_item_page),
            ("📋", self.theme.TINT_BLUE, "Orders", self.theme.TINT_BLUE, self.theme.BLUE,
             "View Order History",
             "See student PDFs, print them with Ctrl+P and update statuses.",
             "Open Orders  →", self.theme.BLUE, self.app.order_screens.view_orders_page),
            ("📢", self.theme.TINT_GREEN, "Notices", self.theme.TINT_GREEN, self.theme.GREEN,
             "Announcements & Maintenance",
             "Post a banner for students or pause new print orders.",
             "Open Notices  →", self.theme.GREEN, self.admin_notices_page),
            ("🧹", self.theme.TINT_ORANGE, "Reset", self.theme.TINT_ORANGE, self.theme.ORANGE,
             "Clear Today's Stats",
             "Reset the dashboard counters. Order History is kept.",
             "Clear Stats  →", self.theme.ORANGE, self.clear_dashboard_stats),
        ])

        # ---------- recent orders ----------
        recent = tk.Frame(
            body, bg=self.theme.SURFACE, padx=22, pady=16,
            highlightbackground=self.theme.BORDER, highlightthickness=1
        )
        recent.pack(fill="x", pady=(0, 24))

        head = tk.Frame(recent, bg=self.theme.SURFACE)
        head.pack(fill="x", pady=(0, 6))

        tk.Label(
            head, text="🧾  Recent Orders",
            font=("Arial", 13, "bold"), bg=self.theme.SURFACE, fg=self.theme.TEXT
        ).pack(side="left")

        view_all = tk.Label(
            head, text="View all  →", font=("Arial", 10, "bold"),
            bg=self.theme.SURFACE, fg=self.theme.PURPLE, cursor="hand2"
        )
        view_all.pack(side="right")
        view_all.bind("<Button-1>", lambda e: self.app.order_screens.view_orders_page())

        latest = list(enumerate(self.services.orders, start=1))[-5:][::-1]

        if not latest:
            tk.Label(
                recent, text="No orders yet. New student orders will show up here.",
                font=("Arial", 10), bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
            ).pack(anchor="w", pady=(6, 4))

        for number, order in latest:
            tk.Frame(recent, bg=self.theme.BORDER, height=1).pack(fill="x")

            row = tk.Frame(recent, bg=self.theme.SURFACE, pady=10)
            row.pack(fill="x")

            is_print = order["type"] == "Printing Service"

            tk.Label(
                row, text="🖨" if is_print else "🛍",
                font=("Segoe UI Emoji", 12),
                bg=self.theme.LIGHT_PURPLE if is_print else self.theme.TINT_ORANGE,
                fg=self.theme.DARK_PURPLE, width=3
            ).pack(side="left", ipady=2)

            info = tk.Frame(row, bg=self.theme.SURFACE)
            info.pack(side="left", padx=(12, 0), fill="x", expand=True)

            details = self.services.order_details_text(order)

            if len(details) > 70:
                details = details[:67] + "..."

            tk.Label(
                info, text=details, font=("Arial", 10, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w"
            ).pack(anchor="w")

            tk.Label(
                info,
                text=(
                    f"Order #{number}  •  "
                    f"{self.services.customer_label(order.get('username', ''))}  •  "
                    f"{order.get('date', 'N/A')}"
                ),
                font=("Arial", 9), bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
            ).pack(anchor="w")

            status = order.get("status", "Pending")
            chip_bg, chip_fg = self.ui.status_style(status)

            tk.Label(
                row, text=self.ui.money(order["total"]), font=("Arial", 11, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.DARK_PURPLE, width=12, anchor="e"
            ).pack(side="right")

            tk.Label(
                row, text=status, font=("Arial", 8, "bold"),
                bg=chip_bg, fg=chip_fg, padx=10, pady=3, width=16
            ).pack(side="right", padx=(0, 14))

    def admin_add_item_page(self):
        if self.app.current_role != "Admin":
            messagebox.showerror(
                "Access Denied",
                "Only the admin can add shop items."
            )
            return

        self.app.clear_content()

        self.ui.page_heading(
            "Add Shop Item",
            "Add new school supplies, or select an item and click Edit to change "
            "its name, price or picture."
        )

        card = self.ui.make_card(self.app.content_frame)
        card.pack(fill="both", expand=True, anchor="n")

        top = tk.Frame(card, bg=self.theme.SURFACE)
        top.pack(fill="x")

        left = tk.Frame(top, bg=self.theme.SURFACE)
        left.pack(side="left", anchor="n")

        right = tk.Frame(top, bg=self.theme.SURFACE)
        right.pack(side="left", anchor="n", padx=45)

        self.ui.make_label(
            left, "Item Name", 12, True
        ).pack(anchor="w", pady=(0, 8))

        item_entry = self.ui.make_entry(left, width=40)
        item_entry.pack(anchor="w", ipady=8, pady=(0, 14))

        self.ui.make_label(
            left, "Item Price (PHP)", 12, True
        ).pack(anchor="w", pady=(0, 8))

        price_entry = self.ui.make_entry(left, width=40)
        price_entry.pack(anchor="w", ipady=8, pady=(0, 14))

        self.ui.make_label(
            left, "Item Picture (optional)", 12, True
        ).pack(anchor="w", pady=(0, 8))

        picture_row = tk.Frame(left, bg=self.theme.SURFACE)
        picture_row.pack(anchor="w")

        selected_picture = {"path": ""}

        preview = tk.Label(
            right,
            image=self.ui.get_thumbnail("", 150),
            bg=self.theme.SURFACE,
            bd=1,
            relief="solid"
        )
        preview.pack()

        self.ui.make_label(
            right, "Picture Preview", 10, False, self.theme.GRAY
        ).pack(pady=(6, 0))

        picture_name = self.ui.make_label(
            picture_row, "No picture chosen", 10, False, self.theme.GRAY
        )

        def choose_picture():
            path = filedialog.askopenfilename(
                title="Choose Item Picture",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                    ("All files", "*.*")
                ]
            )

            if not path:
                return

            try:
                with Image.open(path) as test_image:
                    test_image.verify()

            except (OSError, ValueError):
                messagebox.showerror(
                    "Invalid Picture",
                    "That file is not a valid image."
                )
                return

            selected_picture["path"] = path
            picture_name.config(text=os.path.basename(path))

            # Bypass the cache key reuse problem: always show the new file
            self.ui.image_cache.pop((path, 150), None)
            preview.config(image=self.ui.get_thumbnail(path, 150))

        self.ui.make_button(
            picture_row, "Choose Picture", choose_picture, 16, self.theme.DARK_PURPLE
        ).pack(side="left", padx=(0, 12))

        picture_name.pack(side="left")

        columns = ("Price",)

        tree = ttk.Treeview(
            card,
            columns=columns,
            show="tree headings",
            height=5
        )

        tree.heading("#0", text="Item Name")
        tree.heading("Price", text="Price")

        tree.column("#0", width=300)
        tree.column("Price", width=180, anchor="center")

        tree.pack(fill="x", pady=(18, 15))

        def show_shop_items():
            for row in tree.get_children():
                tree.delete(row)

            for name, price in self.services.shop_items.items():
                tree.insert(
                    "",
                    "end",
                    text=" " + name,
                    image=self.ui.get_thumbnail(self.services.item_images.get(name, ""), 30),
                    values=(self.ui.money(price),)
                )

        editing = {"name": None, "picture": ""}

        def reset_form():
            editing["name"] = None
            editing["picture"] = ""
            item_entry.delete(0, tk.END)
            price_entry.delete(0, tk.END)
            selected_picture["path"] = ""
            picture_name.config(text="No picture chosen")
            preview.config(image=self.ui.get_thumbnail("", 150))
            save_button.config(text="Add Item")
            cancel_button.pack_forget()

        def start_edit(event=None):
            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "No Selection",
                    "Select an item to edit."
                )
                return

            name = str(tree.item(selected[0], "text")).strip()

            if name not in self.services.shop_items:
                return

            reset_form()
            editing["name"] = name
            editing["picture"] = self.services.item_images.get(name, "")

            item_entry.insert(0, name)
            price_entry.insert(0, f"{self.services.shop_items[name]:.2f}")

            picture_name.config(
                text="Current picture (choose a file to replace it)"
                if editing["picture"] else "No picture chosen"
            )
            preview.config(image=self.ui.get_thumbnail(editing["picture"], 150))

            save_button.config(text="Save Changes")
            cancel_button.pack(side="left", padx=10)
            item_entry.focus_set()

        def save_item():
            old_name = editing["name"]

            try:
                name, price = self.services.save_item(
                    old_name, item_entry.get(), price_entry.get(),
                    selected_picture["path"], editing["picture"]
                )
            except ServiceError as error:
                self.app.show_error(error)
                return

            show_shop_items()
            reset_form()

            verb = "updated" if old_name is not None else "added successfully"
            messagebox.showinfo(
                "Success",
                f"{name} has been {verb}!\n"
                f"Price: {self.ui.money(price)}"
            )

        def delete_shop_item():
            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "No Selection",
                    "Select an item to delete."
                )
                return

            name = str(tree.item(selected[0], "text")).strip()

            if name not in self.services.shop_items:
                return

            if not messagebox.askyesno(
                "Delete Item",
                f"Are you sure you want to delete {name}?"
            ):
                return

            try:
                self.services.delete_item(name)
            except ServiceError as error:
                self.app.show_error(error)
                return

            if editing["name"] == name:
                reset_form()

            show_shop_items()

            messagebox.showinfo(
                "Success",
                f"{name} has been removed from the shop."
            )


        buttons = tk.Frame(card, bg=self.theme.SURFACE)
        buttons.pack(anchor="w", pady=(0, 15))

        save_button = self.ui.make_button(
            buttons, "Add Item", save_item, 18, self.theme.GREEN
        )
        save_button.pack(side="left", padx=(0, 10))

        self.ui.make_button(
            buttons, "Edit Selected Item", start_edit, 20, self.theme.BLUE
        ).pack(side="left", padx=10)

        self.ui.make_button(
            buttons, "Delete Selected Item",
            delete_shop_item, 22, self.theme.RED
        ).pack(side="left", padx=10)

        cancel_button = self.ui.make_button(
            buttons, "Cancel Edit", reset_form, 14, self.theme.GRAY
        )

        tree.bind("<Double-1>", start_edit)

        self.ui.make_button(
            card, "Return to Dashboard",
            self.main_menu, 25, self.theme.DARK_PURPLE
        ).pack(anchor="w")

        show_shop_items()

    def admin_notices_page(self):
        if self.app.current_role != "Admin":
            self.app.return_main_menu()
            return

        self.app.clear_content()

        self.ui.page_heading(
            "Announcements & Maintenance",
            "Post an announcement that pops up for students, or pause new print orders."
        )

        self.ui.make_button(
            self.app.content_frame, "⬅  Return to Main Menu",
            self.app.return_main_menu, 24, self.theme.DARK_PURPLE
        ).pack(side="bottom", anchor="e", pady=(14, 0))

        wrap = tk.Frame(self.app.content_frame, bg=self.theme.BG)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1, uniform="notice")
        wrap.columnconfigure(1, weight=1, uniform="notice")
        wrap.rowconfigure(0, weight=1)

        limit = self.services.NOTE_MAX


        ann_card = self.ui.make_card(wrap)
        ann_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.ui.make_label(ann_card, "📢  Announcement", 16, True).pack(anchor="w")
        self.ui.make_label(
            ann_card, "Pops up on each student's screen when they open their dashboard (once per login).",
            10, False, self.theme.GRAY
        ).pack(anchor="w", pady=(2, 12))

        current = self.services.get_announcement()

        self.ui.make_label(
            ann_card,
            f"● Live since {current['date']}" if current
            else "○ No announcement is showing.",
            10, True, self.theme.GREEN if current else self.theme.GRAY
        ).pack(anchor="w", pady=(0, 8))

        ann_buttons = tk.Frame(ann_card, bg=self.theme.SURFACE)
        ann_buttons.pack(fill="x", side="bottom")

        ann_box = self.ui.make_textbox(ann_card, 6, 40)
        ann_box.pack(fill="x")

        if current:
            ann_box.insert("1.0", current["text"])

        ann_counter = self.ui.make_label(ann_card, "", 9, False, self.theme.GRAY)
        ann_counter.pack(anchor="e", pady=(4, 0))

        def update_ann_counter(event=None):
            used = len(ann_box.get("1.0", "end").strip())
            ann_counter.config(
                text=f"{used}/{limit}", fg=self.theme.RED if used > limit else self.theme.GRAY
            )

        ann_box.bind("<KeyRelease>", update_ann_counter)
        update_ann_counter()

        self.ui.make_label(
            ann_card, "Example: Printer is down until 2 PM today.",
            9, False, self.theme.GRAY
        ).pack(anchor="w", pady=(0, 12))

        def post_announcement():
            try:
                self.services.set_announcement(ann_box.get("1.0", "end"), self.app.current_name)
            except ServiceError as error:
                self.app.show_error(error)
                return

            messagebox.showinfo(
                "Announcement Posted",
                "Students will see it as a pop-up when they open their dashboard."
            )
            self.admin_notices_page()

        def remove_announcement():
            if not current:
                return

            try:
                self.services.clear_announcement(self.app.current_name)
            except ServiceError as error:
                self.app.show_error(error)
                return

            self.admin_notices_page()

        self.ui.make_button(
            ann_buttons, "Post Announcement", post_announcement, 20, self.theme.GREEN
        ).pack(side="left")

        self.ui.make_button(
            ann_buttons, "Remove", remove_announcement, 11, self.theme.RED
        ).pack(side="right")


        maint_card = self.ui.make_card(wrap)
        maint_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self.ui.make_label(
            maint_card, "🛠  Printer Maintenance Mode", 16, True
        ).pack(anchor="w")
        self.ui.make_label(
            maint_card,
            "When ON, students cannot place new print orders. "
            "The shop stays open.",
            10, False, self.theme.GRAY
        ).pack(anchor="w", pady=(2, 12))

        maintenance = self.services.get_maintenance()
        maint_var = tk.BooleanVar(value=maintenance["on"])

        self.ui.make_switch(
            maint_card, maint_var,
            "Maintenance mode is ON", "Maintenance mode is OFF"
        ).pack(anchor="w", pady=(0, 14))

        self.ui.make_label(
            maint_card, "Message students will see:", 11, True
        ).pack(anchor="w", pady=(0, 6))

        def save_maintenance():
            try:
                self.services.set_maintenance(
                    maint_var.get(), msg_box.get("1.0", "end"), self.app.current_name
                )
            except ServiceError as error:
                self.app.show_error(error)
                return

            messagebox.showinfo(
                "Saved",
                "Printing is now PAUSED for students." if maint_var.get()
                else "Printing is open again."
            )
            self.admin_notices_page()

        self.ui.make_button(
            maint_card, "Save Maintenance Setting", save_maintenance, 26, self.theme.BLUE
        ).pack(side="bottom", anchor="w")

        msg_box = self.ui.make_textbox(maint_card, 4, 40)
        msg_box.pack(fill="x")
        msg_box.insert("1.0", maintenance["message"])

        self.ui.make_label(
            maint_card,
            "Leave empty to use: \"Printing is temporarily paused for "
            "maintenance. Please try again later.\"",
            9, False, self.theme.GRAY
        ).pack(anchor="w", pady=(6, 12))