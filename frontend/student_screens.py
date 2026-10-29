"""FRONTEND - student pages: home, printing, shop, cart and profile."""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from PIL import Image

from backend.services import ServiceError
from frontend.screen import Screen


class StudentScreens(Screen):
    """Everything a logged-in student can do."""

    PRINT_TYPE_INFO = {
        "Black and White": ("⚫", "Black & White"),
        "Colored": ("🎨", "Full Color")
    }

    def show_announcement_popup(self, announcement):
        """Modal pop-up in the middle of the window (students only)."""
        if self.app.current_role != "Student":
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Announcement")
        dialog.configure(bg=self.theme.SURFACE)
        dialog.transient(self.root)
        dialog.resizable(False, False)

        tk.Frame(dialog, bg=self.theme.BLUE, height=8).pack(fill="x")

        body = tk.Frame(dialog, bg=self.theme.SURFACE, padx=34, pady=24)
        body.pack(fill="both", expand=True)

        head = tk.Frame(body, bg=self.theme.SURFACE)
        head.pack(fill="x")

        tk.Label(
            head, text="📢", font=("Segoe UI Emoji", 26),
            bg=self.theme.TINT_BLUE, fg=self.theme.BLUE, width=3
        ).pack(side="left", ipady=4)

        titles = tk.Frame(head, bg=self.theme.SURFACE)
        titles.pack(side="left", padx=(14, 0))

        tk.Label(
            titles, text="Announcement", font=("Arial", 17, "bold"),
            bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w"
        ).pack(anchor="w")

        tk.Label(
            titles, text=f"Posted {announcement['date']}", font=("Arial", 9),
            bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
        ).pack(anchor="w")

        tk.Label(
            body, text=announcement["text"], font=("Arial", 12),
            bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w", justify="left", wraplength=400
        ).pack(anchor="w", pady=(20, 22))

        self.ui.make_button(body, "Got it", dialog.destroy, 24, self.theme.BLUE).pack(fill="x")

        dialog.update_idletasks()
        width, height = dialog.winfo_reqwidth(), dialog.winfo_reqheight()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - height) // 2
        dialog.geometry(f"+{max(x, 0)}+{max(y, 0)}")

        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.grab_set()
        dialog.focus_set()

    def student_home(self):
        self.app.clear_content()
        self.app.content_frame.config(padx=0, pady=0)   # hero sits flush like the design

        mine = self.app.get_user_orders()
        spent = sum(o["total"] for o in mine)
        cart_count = sum(item["quantity"] for item in self.services.cart)
        pages_printed = sum(
            int(o.get("pages", 0) or 0) * int(o.get("copies", 1) or 1)
            for o in mine if o["type"] == "Printing Service"
        )
        first_name = self.services.students.get(self.app.current_user, {}).get("first", self.app.current_name)

        page = self.ui.make_scroll_page(self.app.content_frame)

        self.ui.make_hero(
            page, f"Hello, {first_name}!", "👋",
            "What would you like to do today?",
            []
        )

        body = tk.Frame(page, bg=self.theme.BG, padx=35)
        body.pack(fill="both", expand=True, pady=(22, 0))

        maintenance = self.services.get_maintenance()
        announcement = self.services.get_announcement()
        noted = self.services.orders_with_notes(self.app.current_user)

        if maintenance["on"]:
            self.ui.build_notice(
                body, "🛠", "Printing is paused",
                self.services.maintenance_message(), self.theme.RED, self.theme.TINT_RED
            )

        # announcements pop up once per login (not as a banner)
        if announcement and self.app.seen["announcement"] != announcement["date"]:
            self.app.seen["announcement"] = announcement["date"]
            self.root.after(900, lambda a=announcement: self.show_announcement_popup(a))

        if noted:
            self.ui.build_banner(
                body, f"💬  {len(noted)} order(s) have a message from the admin",
                "Read in My Order History  →", self.app.order_screens.view_orders_page,
                self.theme.ORANGE, self.theme.TINT_ORANGE
            )

        ready = self.services.ready_orders(self.app.current_user)

        if ready:
            self.ui.build_banner(
                body, f"📦  {len(ready)} order(s) ready for pickup!",
                "View My Order History  →", self.app.order_screens.view_orders_page, self.theme.GREEN, self.theme.TINT_GREEN
            )

        self.ui.build_stat_cards(body, [
            ("TOTAL SPENT", "💳", self.theme.LIGHT_PURPLE, self.theme.PURPLE, self.ui.money(spent),
             f"{len(mine)} order(s) so far", None),
            ("ITEMS IN CART", "🛒", self.theme.TINT_BLUE, self.theme.BLUE, str(cart_count),
             "Ready for checkout" if cart_count else "Your cart is empty",
             ("Cart", self.theme.TINT_BLUE, self.theme.BLUE)),
            ("TOTAL PRINTED", "📄", self.theme.TINT_GREEN, self.theme.GREEN, str(pages_printed),
             "Pages total", None),
        ])

        self.ui.build_action_cards(body, [
            ("⬆", self.theme.LIGHT_PURPLE,
             *(("Paused", self.theme.TINT_RED, self.theme.RED) if maintenance["on"]
               else ("Instant Quote", self.theme.TINT_PURPLE, self.theme.PURPLE)),
             "New Print Job",
             "Upload a PDF, pick black & white or color, and set your copies.",
             "Start Upload  →", self.theme.PURPLE, self.printing_page),
            ("🧺", self.theme.TINT_BLUE, "Store", self.theme.TINT_BLUE, self.theme.BLUE,
             "Buy Supplies",
             "Browse bond paper, ballpens, notebooks and more.",
             "Browse Catalog  →", self.theme.BLUE, self.shop_page),
            ("🛒", self.theme.TINT_ORANGE, "Cart", self.theme.TINT_ORANGE, self.theme.ORANGE,
             "Shopping Cart",
             f"{cart_count} item(s) waiting for checkout."
             if cart_count else "Your cart is empty. Add some supplies!",
             "View Cart  →", self.theme.ORANGE, self.cart_page),
            ("📋", self.theme.TINT_GREEN, "History", self.theme.TINT_GREEN, self.theme.GREEN,
             "My Order History",
             "Review your past print and shop orders and their status.",
             "View Orders  →", self.theme.GREEN, self.app.order_screens.view_orders_page),
        ])

        # ---------- recent activity ----------
        recent = tk.Frame(
            body, bg=self.theme.SURFACE, padx=22, pady=16,
            highlightbackground=self.theme.BORDER, highlightthickness=1
        )
        recent.pack(fill="x", pady=(0, 24))

        recent_head = tk.Frame(recent, bg=self.theme.SURFACE)
        recent_head.pack(fill="x", pady=(0, 6))

        tk.Label(
            recent_head, text="🧾  Recent Activity",
            font=("Arial", 13, "bold"), bg=self.theme.SURFACE, fg=self.theme.TEXT
        ).pack(side="left")

        view_all = tk.Label(
            recent_head, text="View all  →", font=("Arial", 10, "bold"),
            bg=self.theme.SURFACE, fg=self.theme.PURPLE, cursor="hand2"
        )
        view_all.pack(side="right")
        view_all.bind("<Button-1>", lambda e: self.app.order_screens.view_orders_page())

        latest = mine[-3:][::-1]

        if not latest:
            tk.Label(
                recent, text="No orders yet — place your first print order "
                             "or buy some supplies!",
                font=("Arial", 10), bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
            ).pack(anchor="w", pady=(6, 4))

        for order in latest:
            tk.Frame(recent, bg=self.theme.BORDER, height=1).pack(fill="x")

            row = tk.Frame(recent, bg=self.theme.SURFACE, pady=9)
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

            if len(details) > 62:
                details = details[:59] + "..."

            tk.Label(
                info, text=details, font=("Arial", 10, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w"
            ).pack(anchor="w")

            tk.Label(
                info, text=order.get("date", "N/A"), font=("Arial", 9),
                bg=self.theme.SURFACE, fg=self.theme.GRAY, anchor="w"
            ).pack(anchor="w")

            if order.get("note"):
                note_text = order["note"]

                if len(note_text) > 80:
                    note_text = note_text[:77] + "..."

                tk.Label(
                    info, text=f"💬 Admin: {note_text}", font=("Arial", 9, "bold"),
                    bg=self.theme.SURFACE, fg=self.theme.ORANGE, anchor="w"
                ).pack(anchor="w", pady=(2, 0))

            status = order.get("status", "Pending")
            chip_bg, chip_fg = self.ui.status_style(status)

            tk.Label(
                row, text=self.ui.money(order["total"]), font=("Arial", 11, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.DARK_PURPLE, width=12, anchor="e"
            ).pack(side="right")

            tk.Label(
                row, text=status, font=("Arial", 8, "bold"),
                bg=chip_bg, fg=chip_fg, padx=10, pady=3
            ).pack(side="right", padx=(0, 14))

    def printing_page(self):
        if self.app.current_role == "Admin":
            self.app.admin.main_menu()
            return

        self.app.clear_content()

        self.ui.page_heading(
            "Printing Service",
            "Upload your PDF, pick a print type, and set the number of copies."
        )

        paused = self.services.get_maintenance()["on"]

        if paused:
            self.ui.build_notice(
                self.app.content_frame, "🛠", "Printing is paused",
                self.services.maintenance_message(), self.theme.RED, self.theme.TINT_RED
            )

        state = {"path": "", "pages": 0, "type": list(self.services.PRINT_PRICES.keys())[0]}
        copies_var = tk.StringVar(value="1")

        body = tk.Frame(self.app.content_frame, bg=self.theme.BG)
        body.pack(fill="both", expand=True)

        left = tk.Frame(body, bg=self.theme.BG)
        left.pack(side="left", fill="both", expand=True)

        right = self.ui.make_card(body)
        right.configure(width=360)
        right.pack(side="right", fill="y", padx=(22, 0))
        right.pack_propagate(False)

        def step_card(number, title):
            card = self.ui.make_card(left)
            card.configure(pady=16)
            card.pack(fill="x", pady=(0, 14))

            header = tk.Frame(card, bg=self.theme.SURFACE)
            header.pack(fill="x")

            tk.Label(
                header, text=str(number), font=("Arial", 11, "bold"),
                bg=self.theme.PURPLE, fg=self.theme.WHITE, width=3, pady=2
            ).pack(side="left")

            self.ui.make_label(header, title, 14, True).pack(side="left", padx=12)
            return card


        upload_card = step_card(1, "Upload your PDF")

        zone = tk.Frame(
            upload_card, bg=self.theme.LIGHT_PURPLE,
            highlightbackground=self.theme.PURPLE, highlightthickness=1,
            cursor="hand2"
        )
        zone.pack(fill="x", pady=(14, 0))

        zone_icon = tk.Label(
            zone, text="📄", font=("Segoe UI Emoji", 28),
            bg=self.theme.LIGHT_PURPLE, fg=self.theme.DARK_PURPLE, cursor="hand2"
        )
        zone_icon.pack(pady=(14, 0))

        file_label = tk.Label(
            zone, text="Click here to choose a PDF file",
            font=("Arial", 12, "bold"), bg=self.theme.LIGHT_PURPLE, fg=self.theme.DARK_PURPLE,
            cursor="hand2", wraplength=520
        )
        file_label.pack(pady=(4, 0))

        hint_label = tk.Label(
            zone, text="PDF only  •  pages are counted automatically",
            font=("Arial", 10), bg=self.theme.LIGHT_PURPLE, fg=self.theme.GRAY, cursor="hand2"
        )
        hint_label.pack(pady=(2, 14))

        type_card = step_card(2, "Choose print type")

        type_row = tk.Frame(type_card, bg=self.theme.SURFACE)
        type_row.pack(fill="x", pady=(14, 0))

        type_widgets = {}

        def refresh_types():
            for name, (frame, labels, check) in type_widgets.items():
                selected = name == state["type"]
                bg = self.theme.LIGHT_PURPLE if selected else self.theme.SURFACE

                frame.config(
                    bg=bg,
                    highlightbackground=self.theme.PURPLE if selected else self.theme.BORDER,
                    highlightthickness=2 if selected else 1
                )

                for label in labels:
                    label.config(bg=bg)

                check.config(text="✔" if selected else "")

        def select_type(name):
            state["type"] = name
            refresh_types()
            update_summary()

        for column, name in enumerate(self.services.PRINT_PRICES):
            icon, title = self.PRINT_TYPE_INFO.get(name, ("🖨", name))
            type_row.columnconfigure(column, weight=1, uniform="type")

            tile = tk.Frame(
                type_row, bg=self.theme.SURFACE, padx=16, pady=12,
                highlightbackground=self.theme.BORDER, highlightthickness=1,
                cursor="hand2"
            )
            tile.grid(
                row=0, column=column, sticky="nsew",
                padx=(0, 10) if column == 0 else (10, 0)
            )

            icon_lbl = tk.Label(
                tile, text=icon, font=("Segoe UI Emoji", 20),
                bg=self.theme.SURFACE, cursor="hand2"
            )
            icon_lbl.pack(side="left")

            text_box = tk.Frame(tile, bg=self.theme.SURFACE, cursor="hand2")
            text_box.pack(side="left", padx=12)

            title_lbl = tk.Label(
                text_box, text=title, font=("Arial", 12, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.TEXT, anchor="w", cursor="hand2"
            )
            title_lbl.pack(anchor="w")

            price_lbl = tk.Label(
                text_box, text=f"{self.ui.money(self.services.PRINT_PRICES[name])} / page",
                font=("Arial", 10), bg=self.theme.SURFACE, fg=self.theme.GRAY,
                anchor="w", cursor="hand2"
            )
            price_lbl.pack(anchor="w")

            check_lbl = tk.Label(
                tile, text="", font=("Arial", 14, "bold"),
                bg=self.theme.SURFACE, fg=self.theme.PURPLE
            )
            check_lbl.pack(side="right")

            labels = [icon_lbl, text_box, title_lbl, price_lbl, check_lbl]
            type_widgets[name] = (tile, labels, check_lbl)

            for widget in [tile] + labels:
                widget.bind("<Button-1>", lambda e, n=name: select_type(n))

        # ---------- step 3: copies ----------
        copies_card = step_card(3, "Number of copies")

        stepper = tk.Frame(copies_card, bg=self.theme.SURFACE)
        stepper.pack(anchor="w", pady=(14, 0))

        def change_copies(delta):
            try:
                value = int(copies_var.get())
            except ValueError:
                value = 1

            copies_var.set(str(max(1, value + delta)))

        self.ui.make_button(
            stepper, "−", lambda: change_copies(-1), 4, self.theme.DARK_PURPLE
        ).pack(side="left")

        copies_entry = tk.Entry(
            stepper, textvariable=copies_var, width=6, justify="center",
            font=("Arial", 16, "bold"), bg=self.theme.LIGHT_PURPLE, fg=self.theme.DARK_PURPLE,
            relief="flat", insertbackground=self.theme.DARK_PURPLE
        )
        copies_entry.pack(side="left", ipady=9, padx=10)

        self.ui.make_button(
            stepper, "+", lambda: change_copies(1), 4, self.theme.DARK_PURPLE
        ).pack(side="left")

        self.ui.make_label(
            stepper, "copies", 11, False, self.theme.GRAY
        ).pack(side="left", padx=14)

        # ---------- right: order summary ----------
        self.ui.make_label(right, "🧾  Order Summary", 16, True).pack(
            anchor="w", pady=(0, 14)
        )

        def summary_row(title):
            row = tk.Frame(right, bg=self.theme.SURFACE)
            row.pack(fill="x", pady=5)

            self.ui.make_label(row, title, 10, False, self.theme.GRAY).pack(side="left", anchor="n")

            value = tk.Label(
                row, text="—", font=("Arial", 11, "bold"), bg=self.theme.SURFACE,
                fg=self.theme.TEXT, anchor="e", justify="right", wraplength=210
            )
            value.pack(side="right")
            return value

        sum_file = summary_row("File")
        sum_pages = summary_row("Pages")
        sum_type = summary_row("Print type")
        sum_copies = summary_row("Copies")
        sum_price = summary_row("Price per page")

        tk.Frame(right, bg=self.theme.BORDER, height=1).pack(fill="x", pady=14)

        self.ui.make_label(right, "TOTAL", 10, True, self.theme.GRAY).pack(anchor="w")

        total_label = self.ui.make_label(right, self.ui.money(0), 26, True, self.theme.DARK_PURPLE)
        total_label.pack(anchor="w", pady=(2, 4))

        formula_label = self.ui.make_label(right, "", 9, False, self.theme.GRAY)
        formula_label.pack(anchor="w", pady=(0, 14))

        def update_summary(*args):
            price = self.services.PRINT_PRICES[state["type"]]
            pages = state["pages"]

            try:
                copies = int(copies_var.get())
            except ValueError:
                copies = 0

            sum_file.config(
                text=os.path.basename(state["path"]) if state["path"] else "—"
            )
            sum_pages.config(text=str(pages) if pages else "—")
            sum_type.config(text=self.PRINT_TYPE_INFO.get(
                state["type"], ("", state["type"]))[1])
            sum_copies.config(text=str(copies) if copies > 0 else "—")
            sum_price.config(text=self.ui.money(price))

            if pages and copies > 0:
                total_label.config(text=self.ui.money(price * pages * copies))
                formula_label.config(
                    text=f"{pages} pages × {copies} copies × {self.ui.money(price)}"
                )
            else:
                total_label.config(text=self.ui.money(0))
                formula_label.config(text="Upload a PDF and set copies")

        copies_var.trace_add("write", update_summary)

        def browse_pdf(event=None):
            path = filedialog.askopenfilename(
                title="Choose a PDF file",
                filetypes=[("PDF files", "*.pdf")]
            )

            if not path:
                return

            try:
                pages = self.printing.count_pdf_pages(path)

            except Exception as error:
                messagebox.showerror(
                    "PDF Error",
                    f"Could not read this PDF.\n{error}"
                )
                return

            state["path"] = path
            state["pages"] = pages

            zone_icon.config(text="✅")
            file_label.config(text=os.path.basename(path))
            hint_label.config(
                text=f"{pages} page(s)  •  click to choose a different file"
            )
            update_summary()

        for widget in (zone, zone_icon, file_label, hint_label):
            widget.bind("<Button-1>", browse_pdf)

        def submit_print_order():
            if not state["path"]:
                messagebox.showerror(
                    "Missing Information",
                    "Please choose a PDF file to print."
                )
                return

            try:
                copies = int(copies_var.get())

                if copies <= 0:
                    raise ValueError

            except ValueError:
                messagebox.showerror(
                    "Invalid Copies",
                    "Enter a positive whole number."
                )
                return

            selected_type = state["type"]
            pages = state["pages"]

            try:
                order = self.services.create_print_order(
                    self.app.current_user, state["path"], pages, selected_type, copies
                )
            except ServiceError as error:
                self.app.show_error(error)
                return

            receipt = (
                "PRINTING RECEIPT\n"
                "------------------------------\n"
                f"Student: {self.app.current_name} ({self.app.current_user})\n"
                f"File: {order['filename']}\n"
                f"Type: {selected_type}\n"
                f"Pages: {pages}\n"
                f"Copies: {copies}\n"
                f"Price per page: {self.ui.money(self.services.PRINT_PRICES[selected_type])}\n"
                "------------------------------\n"
                f"TOTAL: {self.ui.money(order['total'])}\n"
                f"Date: {order['date']}\n\n"
                "Your PDF was sent to the admin for printing."
            )

            messagebox.showinfo("Receipt", receipt)

            if messagebox.askyesno(
                "New Order",
                "Would you like to create another print order?"
            ):
                self.printing_page()
            else:
                self.app.return_main_menu()

        submit_button = self.ui.make_button(
            right, "🖨  Submit Print Order", submit_print_order, 24, self.theme.GREEN
        )
        submit_button.pack(fill="x", pady=(0, 10))

        if paused:
            submit_button.unbind("<Enter>")
            submit_button.unbind("<Leave>")
            submit_button.config(
                text="⏸  Printing Paused", state="disabled", bg=self.theme.GRAY,
                disabledforeground=self.theme.WHITE, cursor="arrow"
            )

        self.ui.make_button(
            right, "Return to Main Menu", self.app.return_main_menu, 24, self.theme.DARK_PURPLE
        ).pack(fill="x")

        refresh_types()
        update_summary()

    def shop_page(self):
        if self.app.current_role == "Admin":
            self.app.admin.main_menu()
            return

        self.app.clear_content()

        self.ui.page_heading(
            "School Supplies Shop",
            "Browse the items and add them to your cart."
        )

        top = tk.Frame(self.app.content_frame, bg=self.theme.BG)
        top.pack(fill="x", pady=(0, 12))

        self.ui.make_button(
            top, "View Shopping Cart", self.cart_page, 22
        ).pack(side="left", padx=(0, 10))

        self.ui.make_button(
            top, "Return to Main Menu", self.app.return_main_menu, 22, self.theme.DARK_PURPLE
        ).pack(side="left")

        shop_card = tk.Frame(
            self.app.content_frame,
            bg=self.theme.SURFACE,
            highlightbackground=self.theme.BORDER,
            highlightthickness=1
        )
        shop_card.pack(fill="both", expand=True)

        if not self.services.shop_items:
            self.ui.make_label(
                shop_card,
                "No items available. Please ask the admin to add items.",
                12,
                False,
                self.theme.RED
            ).pack(anchor="w", padx=25, pady=25)
            return

        canvas = tk.Canvas(shop_card, bg=self.theme.SURFACE, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            shop_card, orient="vertical", command=canvas.yview
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        grid_frame = tk.Frame(canvas, bg=self.theme.SURFACE)
        window_id = canvas.create_window((0, 0), window=grid_frame, anchor="nw")

        grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(window_id, width=e.width)
        )

        def on_mousewheel(event):
            try:
                if not canvas.winfo_exists():
                    return

                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
                else:
                    canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

            except tk.TclError:
                pass

        self.root.bind_all("<MouseWheel>", on_mousewheel)
        self.root.bind_all("<Button-4>", on_mousewheel)
        self.root.bind_all("<Button-5>", on_mousewheel)

        def add_to_cart(name, quantity_entry):
            try:
                quantity = self.services.add_to_cart(name, quantity_entry.get())
            except ServiceError as error:
                self.app.show_error(error)
                return

            messagebox.showinfo(
                "Shopping Cart",
                f"{quantity} x {name} added to cart."
            )

            quantity_entry.delete(0, tk.END)
            quantity_entry.insert(0, "1")

        columns = 4

        for col in range(columns):
            grid_frame.columnconfigure(col, weight=1, uniform="tile")

        for index, (name, price) in enumerate(self.services.shop_items.items()):
            tile = tk.Frame(
                grid_frame,
                bg=self.theme.SURFACE,
                padx=12,
                pady=12,
                highlightbackground=self.theme.BORDER,
                highlightthickness=1
            )
            tile.grid(
                row=index // columns,
                column=index % columns,
                padx=10,
                pady=10,
                sticky="nsew"
            )

            tk.Label(
                tile,
                image=self.ui.get_thumbnail(self.services.item_images.get(name, ""), 170),
                bg=self.theme.SURFACE,
                bd=0
            ).pack()

            tk.Label(
                tile,
                text=name,
                font=("Arial", 12, "bold"),
                bg=self.theme.SURFACE,
                fg=self.theme.TEXT,
                wraplength=170
            ).pack(pady=(10, 2))

            tk.Label(
                tile,
                text=self.ui.money(price),
                font=("Arial", 12, "bold"),
                bg=self.theme.SURFACE,
                fg=self.theme.DARK_PURPLE
            ).pack(pady=(0, 8))

            qty_row = tk.Frame(tile, bg=self.theme.SURFACE)
            qty_row.pack(pady=(0, 8))

            tk.Label(
                qty_row, text="Qty:", font=("Arial", 11),
                bg=self.theme.SURFACE, fg=self.theme.TEXT
            ).pack(side="left", padx=(0, 6))

            qty_entry = self.ui.make_entry(qty_row, width=6)
            qty_entry.insert(0, "1")
            qty_entry.pack(side="left", ipady=4)

            self.ui.make_button(
                tile,
                "Add to Cart",
                lambda n=name, e=qty_entry: add_to_cart(n, e),
                16
            ).pack()

    def cart_page(self):
        if self.app.current_role == "Admin":
            self.app.admin.main_menu()
            return

        self.app.clear_content()

        self.ui.page_heading(
            "Shopping Cart",
            "Review your items before checkout."
        )

        card = self.ui.make_card(self.app.content_frame)
        card.pack(fill="both", expand=True)

        columns = ("Item", "Quantity", "Price", "Subtotal")

        tree_frame = tk.Frame(card, bg=self.theme.SURFACE)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=12
        )

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=180)

        tree.tag_configure("even", background=self.theme.SURFACE)
        tree.tag_configure("odd", background=self.theme.STRIPE)

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row, item in enumerate(self.services.cart):
            tree.insert(
                "",
                "end",
                tags=("even" if row % 2 == 0 else "odd",),
                values=(
                    item["item"],
                    item["quantity"],
                    self.ui.money(item["price"]),
                    self.ui.money(item["subtotal"])
                )
            )

        total = sum(item["subtotal"] for item in self.services.cart)

        self.ui.make_label(
            card, f"TOTAL: {self.ui.money(total)}", 19, True, self.theme.DARK_PURPLE
        ).pack(anchor="e", pady=20)

        buttons = tk.Frame(card, bg=self.theme.SURFACE)
        buttons.pack(anchor="w")

        def remove_item():
            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Notice",
                    "Select an item to remove."
                )
                return

            self.services.remove_from_cart(str(tree.item(selected[0], "values")[0]))
            self.cart_page()

        def checkout():
            if not self.services.cart:
                messagebox.showwarning(
                    "Empty Cart",
                    "Your shopping cart is empty."
                )
                return

            if not messagebox.askyesno(
                "Confirm Checkout",
                f"Total: {self.ui.money(self.services.cart_total())}\n"
                "Proceed with checkout?"
            ):
                return

            try:
                order = self.services.checkout(self.app.current_user)
            except ServiceError as error:
                self.app.show_error(error)
                return

            receipt = (
                "SHOP RECEIPT\n"
                "------------------------------\n"
                f"Student: {self.app.current_name} ({self.app.current_user})\n"
            )

            for item in order["items"]:
                receipt += (
                    f"{item['item']} x {item['quantity']} = "
                    f"{self.ui.money(item['subtotal'])}\n"
                )

            receipt += (
                "------------------------------\n"
                f"TOTAL: {self.ui.money(order['total'])}\n"
                f"Date: {order['date']}"
            )

            messagebox.showinfo("Receipt", receipt)
            self.app.return_main_menu()

        self.ui.make_button(
            buttons, "Remove Selected Item",
            remove_item, 23, self.theme.RED
        ).pack(side="left", padx=(0, 10))

        self.ui.make_button(
            buttons, "Checkout", checkout, 18, self.theme.GREEN
        ).pack(side="left", padx=10)

        self.ui.make_button(
            card, "Return to Main Menu",
            self.app.return_main_menu, 25, self.theme.DARK_PURPLE
        ).pack(anchor="w", pady=(15, 0))

    def profile_page(self):
        if self.app.current_role != "Student":
            self.app.return_main_menu()
            return

        self.app.clear_content()

        self.ui.page_heading(
            "My Profile", "Add your picture and review your account details."
        )

        self.ui.make_button(
            self.app.content_frame, "⬅  Return to Main Menu",
            self.app.return_main_menu, 24, self.theme.DARK_PURPLE
        ).pack(side="bottom", anchor="e", pady=(14, 0))

        wrap = tk.Frame(self.app.content_frame, bg=self.theme.BG)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1, uniform="profile")
        wrap.columnconfigure(1, weight=2, uniform="profile")
        wrap.rowconfigure(0, weight=1)

        info = self.services.students.get(self.app.current_user, {})
        mine = self.app.get_user_orders()
        picture = self.services.profile_picture(self.app.current_user)

        # ---------- picture card ----------
        left = self.ui.make_card(wrap)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        photo_box = tk.Canvas(
            left, width=180, height=180, bg=self.theme.SURFACE, highlightthickness=0
        )
        photo_box.pack(pady=(10, 14))
        self.ui.draw_avatar(photo_box, 180, picture, self.ui.student_initials(), self.theme.PURPLE, self.theme.PURPLE, 44)

        if not picture:
            photo_box.delete("all")
            photo_box.create_oval(
                4, 4, 176, 176, fill=self.theme.PURPLE, outline=self.theme.LIGHT_PURPLE, width=4
            )
            photo_box.create_text(
                90, 90, text=self.ui.student_initials(), fill=self.theme.WHITE,
                font=("Arial", 44, "bold")
            )

        self.ui.make_label(left, self.app.current_name, 16, True).pack()
        self.ui.make_label(left, f"ID: {self.app.current_user}", 10, False, self.theme.GRAY).pack(
            pady=(2, 16)
        )

        def refresh_everywhere():
            self.app.open_system(rebuild=True)
            self.profile_page()

        def choose_picture():
            path = filedialog.askopenfilename(
                title="Choose your profile picture",
                filetypes=[
                    ("Pictures", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                    ("All files", "*.*")
                ]
            )

            if not path:
                return

            try:
                with Image.open(path) as test:
                    test.verify()
            except Exception:
                messagebox.showerror(
                    "Invalid Picture", "That file is not a readable image."
                )
                return

            try:
                self.services.set_profile_picture(self.app.current_user, path)
            except ServiceError as error:
                self.app.show_error(error)
                return

            refresh_everywhere()

        def remove_picture():
            if not picture:
                return

            if not messagebox.askyesno(
                "Remove Picture", "Remove your profile picture?"
            ):
                return

            try:
                self.services.remove_profile_picture(self.app.current_user)
            except ServiceError as error:
                self.app.show_error(error)
                return

            refresh_everywhere()

        self.ui.make_button(
            left, "📷  Choose Picture" if not picture else "📷  Change Picture",
            choose_picture, 22, self.theme.PURPLE
        ).pack(fill="x", pady=(0, 8))

        if picture:
            self.ui.make_button(
                left, "🗑  Remove Picture", remove_picture, 22, self.theme.RED
            ).pack(fill="x")

        self.ui.make_label(
            left, "PNG, JPG, GIF, BMP or WEBP, up to 8 MB.", 9, False, self.theme.GRAY
        ).pack(pady=(14, 0))


        def change_id_dialog():
            dialog = tk.Toplevel(self.root)
            dialog.title("Change ID Number")
            dialog.configure(bg=self.theme.SURFACE)
            dialog.transient(self.root)
            dialog.resizable(False, False)

            self.ui.make_label(dialog, "Change ID Number", 16, True).pack(
                anchor="w", padx=28, pady=(24, 2)
            )
            self.ui.make_label(
                dialog,
                "Your orders and profile picture stay with your account.",
                9, False, self.theme.GRAY
            ).pack(anchor="w", padx=28, pady=(0, 14))

            self.ui.make_label(dialog, "Current ID", 10, True).pack(anchor="w", padx=28)
            self.ui.make_label(dialog, self.app.current_user, 12, False, self.theme.GRAY).pack(
                anchor="w", padx=28, pady=(2, 10)
            )

            self.ui.make_label(dialog, "New ID number", 10, True).pack(
                anchor="w", padx=28
            )
            new_entry = self.ui.make_entry(dialog, width=34)
            new_entry.pack(padx=28, pady=(4, 2), ipady=7, fill="x")
            self.ui.make_label(
                dialog, "3-20 characters: letters, numbers or dashes.",
                9, False, self.theme.GRAY
            ).pack(anchor="w", padx=28, pady=(0, 10))

            self.ui.make_label(
                dialog, "Current password (to confirm)", 10, True
            ).pack(anchor="w", padx=28)
            password_box, password_entry = self.ui.make_password_field(dialog, 7)
            password_box.pack(padx=28, pady=(4, 0), fill="x")

            def save_new_id(event=None):

                try:
                    new_id = self.services.change_student_id(
                        self.app.current_user, new_entry.get(), password_entry.get()
                    )
                except ServiceError as error:
                    messagebox.showerror(
                        error.title, error.message, parent=dialog
                    )
                    return

                self.app.current_user = new_id
                dialog.destroy()
                messagebox.showinfo(
                    "ID Changed", f"Your ID number is now {new_id}."
                )
                self.app.open_system(rebuild=True)
                self.profile_page()

            self.ui.make_button(
                dialog, "Save New ID", save_new_id, 24, self.theme.GREEN
            ).pack(padx=28, pady=(22, 24), fill="x")

            dialog.bind("<Return>", save_new_id)
            dialog.bind("<Escape>", lambda e: dialog.destroy())
            dialog.grab_set()
            new_entry.focus_set()

        def edit_info_dialog():
            current = self.services.students.get(self.app.current_user, {})

            dialog = tk.Toplevel(self.root)
            dialog.title("Edit Student Information")
            dialog.configure(bg=self.theme.SURFACE)
            dialog.transient(self.root)
            dialog.resizable(False, False)

            self.ui.make_label(dialog, "Edit Student Information", 16, True).pack(
                anchor="w", padx=28, pady=(24, 2)
            )
            self.ui.make_label(
                dialog,
                "Your orders stay with your account. "
                "To change your ID number, use \"Change ID\".",
                9, False, self.theme.GRAY
            ).pack(anchor="w", padx=28, pady=(0, 14))

            self.ui.make_label(dialog, "First name", 10, True).pack(anchor="w", padx=28)
            first_entry = self.ui.make_entry(dialog, width=34)
            first_entry.insert(0, current.get("first", ""))
            first_entry.pack(padx=28, pady=(4, 10), ipady=7, fill="x")

            self.ui.make_label(dialog, "Last name", 10, True).pack(anchor="w", padx=28)
            last_entry = self.ui.make_entry(dialog, width=34)
            last_entry.insert(0, current.get("last", ""))
            last_entry.pack(padx=28, pady=(4, 0), ipady=7, fill="x")

            def save_info(event=None):

                try:
                    first, last = self.services.update_student_info(
                        self.app.current_user, first_entry.get(), last_entry.get()
                    )
                except ServiceError as error:
                    messagebox.showerror(
                        error.title, error.message, parent=dialog
                    )
                    return

                self.app.current_name = f"{first} {last}"
                dialog.destroy()
                messagebox.showinfo(
                    "Information Updated", "Your information was saved."
                )
                self.app.open_system(rebuild=True)
                self.profile_page()

            self.ui.make_button(
                dialog, "Save Changes", save_info, 24, self.theme.GREEN
            ).pack(padx=28, pady=(22, 24), fill="x")

            dialog.bind("<Return>", save_info)
            dialog.bind("<Escape>", lambda e: dialog.destroy())
            dialog.grab_set()
            first_entry.focus_set()


        right = self.ui.make_card(wrap)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self.ui.make_label(right, "Account Details", 16, True).pack(anchor="w")
        self.ui.make_label(
            right, "Your registered information.", 10, False, self.theme.GRAY
        ).pack(anchor="w", pady=(2, 14))

        pages_printed = sum(
            int(o.get("pages", 0) or 0) * int(o.get("copies", 1) or 1)
            for o in mine if o["type"] == "Printing Service"
        )

        details = [
            ("First name", info.get("first", "N/A")),
            ("Last name", info.get("last", "N/A")),
            ("ID number", self.app.current_user),
            ("Orders placed", str(len(mine))),
            ("Pages printed", str(pages_printed)),
            ("Total spent", self.ui.money(sum(o["total"] for o in mine))),
        ]

        for label, value in details:
            tk.Frame(right, bg=self.theme.BORDER, height=1).pack(fill="x")

            row = tk.Frame(right, bg=self.theme.SURFACE, pady=11)
            row.pack(fill="x")

            tk.Label(
                row, text=label, font=("Arial", 10), bg=self.theme.SURFACE, fg=self.theme.GRAY,
                width=16, anchor="w"
            ).pack(side="left")

            tk.Label(
                row, text=value, font=("Arial", 11, "bold"), bg=self.theme.SURFACE,
                fg=self.theme.TEXT, anchor="w"
            ).pack(side="left")

            if label == "First name":
                edit_link = tk.Label(
                    row, text="✏  Edit Information", font=("Arial", 10, "bold"),
                    bg=self.theme.SURFACE, fg=self.theme.PURPLE, cursor="hand2"
                )
                edit_link.pack(side="right")
                edit_link.bind("<Button-1>", lambda e: edit_info_dialog())

            if label == "ID number":
                change_link = tk.Label(
                    row, text="✏  Change ID", font=("Arial", 10, "bold"),
                    bg=self.theme.SURFACE, fg=self.theme.PURPLE, cursor="hand2"
                )
                change_link.pack(side="right")
                change_link.bind("<Button-1>", lambda e: change_id_dialog())