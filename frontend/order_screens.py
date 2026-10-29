"""FRONTEND - the Order History page (used by students and the admin)."""
import tkinter as tk
from tkinter import ttk, messagebox

from backend.services import ServiceError
from frontend.screen import Screen


class OrderScreens(Screen):
    """Order history for both roles."""

    NOTE_TEMPLATES = [
        "File is blurry, please re-upload it.",
        "Wrong page count. Please resubmit the file.",
        "Please come to the counter to confirm your order.",
        "Ready for pickup at the counter until 5 PM.",
    ]

    def view_orders_page(self):
        self.app.clear_content()
        is_admin = self.app.current_role == "Admin"

        if is_admin:
            self.ui.page_heading(
                "Order History",
                "Double-click an order for details. Select a print order and "
                "press Ctrl + P to print its PDF."
            )
        else:
            self.ui.page_heading("My Order History", "View your own orders.")

        card = self.ui.make_card(self.app.content_frame)
        card.pack(fill="both", expand=True)

        toolbar = tk.Frame(card, bg=self.theme.SURFACE)
        toolbar.pack(fill="x", pady=(0, 14))

        self.ui.make_label(toolbar, "🔍 Search", 11, True).pack(side="left", padx=(0, 8))

        search_entry = self.ui.make_entry(toolbar, width=30)
        search_entry.pack(side="left", ipady=6)

        type_filter = ttk.Combobox(
            toolbar,
            values=["All", "Printing Service", "Shop Order"],
            state="readonly",
            width=18,
            font=("Arial", 11)
        )
        type_filter.current(0)
        type_filter.pack(side="left", padx=12, ipady=3)

        count_label = self.ui.make_label(toolbar, "", 11, True, self.theme.DARK_PURPLE)
        count_label.pack(side="right")

        # ---------- buttons (packed first so they never get cut off) ----------
        button_row = tk.Frame(card, bg=self.theme.SURFACE)
        button_row.pack(side="bottom", fill="x", pady=(15, 0))

        # ---------- table ----------
        columns = (
            "Order #", "Customer", "Type", "Details", "Total", "Status",
            "Note", "Date"
        )

        tree_frame = tk.Frame(card, bg=self.theme.SURFACE)
        tree_frame.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            height=8,
            selectmode="extended" if is_admin else "browse"
        )

        widths = {
            "Order #": 70, "Customer": 150, "Type": 130,
            "Details": 270, "Total": 100, "Status": 120, "Note": 60,
            "Date": 130
        }

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=widths[col])

        tree.tag_configure("even", background=self.theme.SURFACE)
        tree.tag_configure("odd", background=self.theme.STRIPE)
        tree.tag_configure("note", foreground=self.theme.ORANGE)

        scrollbar = ttk.Scrollbar(
            tree_frame, orient="vertical", command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        visible_orders = list(self.app.get_user_orders())
        numbers = {id(o): n for n, o in enumerate(visible_orders, start=1)}
        shown = []   # orders currently displayed (row iid = index in this list)

        def refresh_rows(event=None):
            for row in tree.get_children():
                tree.delete(row)

            shown.clear()
            term = search_entry.get().strip().lower()
            kind = type_filter.get()

            for order in visible_orders:
                if kind != "All" and order["type"] != kind:
                    continue

                details = self.services.order_details_text(order)
                haystack = (
                    f"{order.get('username', '')} "
                    f"{self.services.customer_label(order.get('username', ''))} {order['type']} "
                    f"{details} {order.get('date', '')}"
                ).lower()

                if term and term not in haystack:
                    continue

                tag = "even" if len(shown) % 2 == 0 else "odd"

                tree.insert(
                    "", "end", iid=str(len(shown)),
                    tags=(tag, "note") if order.get("note") else (tag,),
                    values=(
                        numbers[id(order)],
                        self.services.customer_label(order.get("username", "")),
                        order["type"],
                        details,
                        self.ui.money(order["total"]),
                        order.get("status", "Pending"),
                        "💬" if order.get("note") else "",
                        order.get("date", "N/A")
                    )
                )
                shown.append(order)

            count_label.config(text=f"{len(shown)} order(s)")

        def selected_orders():
            return [shown[int(i)] for i in tree.selection()]


        def show_order_details(event=None):
            picked = selected_orders()

            if not picked:
                return

            order = picked[0]
            username = order.get("username", "N/A")

            receipt = (
                f"ORDER #{numbers[id(order)]}\n"
                f"Customer: {self.services.customer_label(username)} ({username})\n"
                f"Type: {order['type']}\n"
                f"Date: {order.get('date', 'N/A')}\n"
                "------------------------------\n"
            )

            if order["type"] == "Printing Service":
                pages = order.get("pages", 1)
                unit_price = order["total"] / (order["copies"] * pages)

                receipt += (
                    f"File: {order['filename']}\n"
                    f"Print Type: {order['print_type']}\n"
                    f"Pages: {pages}\n"
                    f"Copies: {order['copies']}\n"
                    f"Price per page: {self.ui.money(unit_price)}\n"
                )
            else:
                for item in order["items"]:
                    receipt += (
                        f"{item['item']} x {item['quantity']} = "
                        f"{self.ui.money(item['subtotal'])}\n"
                    )

            receipt += (
                "------------------------------\n"
                f"TOTAL: {self.ui.money(order['total'])}"
            )

            if order.get("note"):
                receipt += (
                    "\n------------------------------\n"
                    f"MESSAGE FROM ADMIN:\n{order['note']}"
                )

            messagebox.showinfo("Order Details", receipt)

        def open_order_pdf():
            picked = [
                o for o in selected_orders()
                if o["type"] == "Printing Service"
            ]

            if not picked:
                messagebox.showwarning(
                    "No Print Order", "Select a printing order first."
                )
                return

            self.app.open_file(picked[0].get("pdf_path", ""))

        def print_selected_pdf():
            picked = [
                o for o in selected_orders()
                if o["type"] == "Printing Service"
            ]

            if not picked:
                messagebox.showwarning(
                    "No Print Order",
                    "Select one or more printing orders to print."
                )
                return

            if self.app.printer_state["name"] is None and not messagebox.askyesno(
                "No Printer Detected",
                "No printer is connected right now.\n"
                "Try to print anyway?"
            ):
                return

            summary = "\n".join(
                f"• {o['filename']}  ({o['copies']} copies)" for o in picked
            )

            if not messagebox.askyesno(
                "Print PDF", f"Send these files to the printer?\n\n{summary}"
            ):
                return

            done = 0

            for order in picked:
                if self.app.print_file(order.get("pdf_path", ""), order["copies"]):
                    done += 1

            if done:
                self.services.log_activity(
                    self.app.current_name, "PDF printed",
                    ", ".join(
                        f"{self.services.order_label(o)} x{o['copies']}"
                        for o in picked
                    )
                )
                messagebox.showinfo(
                    "Printing", f"{done} file(s) sent to the printer."
                )

        def delete_selected_orders():
            picked = selected_orders()

            if not picked:
                messagebox.showwarning(
                    "No Selection", "Select the order(s) you want to delete."
                )
                return

            if not messagebox.askyesno(
                "Delete Order",
                f"Delete {len(picked)} selected order(s)?\n"
                "Any uploaded PDF for these orders will also be removed.\n"
                "This cannot be undone."
            ):
                return

            try:
                self.services.delete_orders(picked, self.app.current_name)
            except ServiceError as error:
                self.app.show_error(error)

            self.view_orders_page()

        def update_status():
            picked = selected_orders()

            if not picked:
                messagebox.showwarning(
                    "No Selection", "Select the order(s) to update."
                )
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("Update Order Status")
            dialog.configure(bg=self.theme.SURFACE)
            dialog.transient(self.root)
            dialog.resizable(False, False)

            self.ui.make_label(
                dialog, f"Set status for {len(picked)} order(s):", 11, True
            ).pack(anchor="w", padx=26, pady=(22, 8))

            status_box = ttk.Combobox(
                dialog, values=list(self.services.ORDER_STATUSES), state="readonly",
                font=("Arial", 12), width=24
            )
            status_box.set(picked[0].get("status", "Pending"))
            status_box.pack(padx=26, ipady=4)

            def apply_status():
                try:
                    self.services.set_order_status(picked, status_box.get(), self.app.current_name)
                except ServiceError as error:
                    self.app.show_error(error)
                    return

                dialog.destroy()
                self.view_orders_page()

            self.ui.make_button(
                dialog, "Save Status", apply_status, 24, self.theme.GREEN
            ).pack(padx=26, pady=22, fill="x")

            dialog.grab_set()

        def add_note():
            picked = selected_orders()

            if not picked:
                messagebox.showwarning(
                    "No Selection", "Select the order(s) to leave a note on."
                )
                return

            dialog = tk.Toplevel(self.root)
            dialog.title("Order Note")
            dialog.configure(bg=self.theme.SURFACE)
            dialog.transient(self.root)
            dialog.resizable(False, False)

            self.ui.make_label(
                dialog,
                f"Note for {len(picked)} order(s). The student will see it:",
                11, True
            ).pack(anchor="w", padx=26, pady=(22, 8))

            box = self.ui.make_textbox(dialog, 5, 50)
            box.pack(padx=26)
            box.insert("1.0", picked[0].get("note", ""))

            self.ui.make_label(
                dialog, "Quick notes (click to use):", 9, False, self.theme.GRAY
            ).pack(anchor="w", padx=26, pady=(12, 4))

            def use_template(text):
                box.delete("1.0", "end")
                box.insert("1.0", text)

            for text in self.NOTE_TEMPLATES:
                quick = tk.Label(
                    dialog, text=text, font=("Arial", 9), bg=self.theme.LIGHT_PURPLE,
                    fg=self.theme.DARK_PURPLE, anchor="w", padx=10, pady=4, cursor="hand2"
                )
                quick.pack(fill="x", padx=26, pady=2)
                quick.bind("<Button-1>", lambda e, t=text: use_template(t))

            def save_note(clear=False):
                text = "" if clear else box.get("1.0", "end").strip()

                if not clear and not text:
                    messagebox.showwarning(
                        "Empty Note", "Type a note, or use Clear Note.",
                        parent=dialog
                    )
                    return

                try:
                    self.services.set_order_note(picked, text, self.app.current_name)
                except ServiceError as error:
                    self.app.show_error(error)
                    return

                dialog.destroy()
                self.view_orders_page()

            actions = tk.Frame(dialog, bg=self.theme.SURFACE)
            actions.pack(fill="x", padx=26, pady=(16, 22))

            self.ui.make_button(
                actions, "Save Note", save_note, 16, self.theme.GREEN
            ).pack(side="left")

            self.ui.make_button(
                actions, "Clear Note", lambda: save_note(True), 14, self.theme.RED
            ).pack(side="right")

            dialog.grab_set()

        tree.bind("<Double-1>", show_order_details)
        search_entry.bind("<KeyRelease>", refresh_rows)
        type_filter.bind("<<ComboboxSelected>>", refresh_rows)


        self.ui.make_button(
            button_row, "🔄  Refresh", self.view_orders_page, 12
        ).pack(side="left", padx=(0, 10))

        if is_admin:
            self.ui.make_button(
                button_row, "📄  Open PDF", open_order_pdf, 13, self.theme.DARK_PURPLE
            ).pack(side="left", padx=10)

            self.ui.make_button(
                button_row, "🖨  Print PDF (Ctrl+P)",
                print_selected_pdf, 20, self.theme.GREEN
            ).pack(side="left", padx=10)

            self.ui.make_button(
                button_row, "🗑  Delete",
                delete_selected_orders, 11, self.theme.RED
            ).pack(side="left", padx=10)

            tree.bind("<Delete>", lambda e: delete_selected_orders())
            self.app.order_actions["print"] = print_selected_pdf

            self.ui.make_button(
                button_row, "📌  Update Status", update_status, 15, self.theme.BLUE
            ).pack(side="left", padx=10)

            self.ui.make_button(
                button_row, "💬  Add Note", add_note, 13, self.theme.ORANGE
            ).pack(side="left", padx=10)

        self.ui.make_button(
            button_row, "⬅  Return to Main Menu",
            self.app.return_main_menu, 20, self.theme.DARK_PURPLE
        ).pack(side="right")

        refresh_rows()