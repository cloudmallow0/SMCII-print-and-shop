"""BACKEND - business rules. The frontend talks only to `Services`.

Problems the user should see are raised as ServiceError(title, message).
The shared lists / dicts (orders, cart, students, ...) live on the Services
object and are mutated in place, never re-assigned, so the frontend can keep
references to them.

Class layout (one object, built from small focused classes):

    BaseService     state, activity log, load / save everything
    NoticeService   announcement + maintenance mode
    AccountService  login, register, profile, edit information
    OrderService    orders, statuses, notes, dashboard numbers
    ShopService     cart, checkout, shop items
    Services        the object the frontend creates
"""
import os
import re
import secrets
from datetime import datetime

from database.storage import Database


class ServiceError(Exception):
    def __init__(self, title, message):
        super().__init__(message)
        self.title = title
        self.message = message


class BaseService:
    """Shared state, the activity log, and load / save everything."""

    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "1234"

    PRINT_PRICES = {
        "Black and White": 2.00,   # price per PAGE
        "Colored": 5.00,
    }

    ORDER_STATUSES = Database.ORDER_STATUSES
    READY_STATUS = "Ready for Pickup"
    ADMIN_LABEL = "Admin"
    NOTE_MAX = 300

    PICTURE_TYPES = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
    PICTURE_MAX_BYTES = 8 * 1024 * 1024

    def __init__(self, db=None):
        self.db = db or Database()

        self.orders = []
        self.cart = []
        self.students = {}          # id_number -> {"first", "last", "password"}
        self.shop_items = {}        # name -> price
        self.item_images = {}       # name -> image path
        self.stats = {"since": ""}  # orders dated after this count on the dashboard
        self.profile_pics = {}      # id_number -> stored picture path

    def _now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")

    def _file_error(self, what, error):
        return ServiceError("File Error", f"Could not {what}.\n{error}")

    def order_number(self, order):
        for number, other in enumerate(self.orders, start=1):
            if other is order:
                return number

        return 0

    def order_label(self, order):
        """Short text used in the activity log, e.g. 'Order #4 (Resume.pdf)'."""
        if order["type"] == "Printing Service":
            what = order.get("filename", "")
        else:
            what = ", ".join(i["item"] for i in order.get("items", []))[:40]

        return f"Order #{self.order_number(order)} ({what})"

    def log_activity(self, actor, action, details=""):
        """Never raises: a log problem must not block the real action."""
        try:
            self.db.append_log(self._now(), actor or self.ADMIN_LABEL, action, details)
        except OSError:
            pass

    def get_activity_log(self, limit=300):
        try:
            return self.db.load_log(limit)
        except OSError:
            return []

    def init(self):
        """Load everything from the database. Returns a list of warnings."""
        warnings = []

        try:
            self.students.update(self.db.load_students())
        except OSError as e:
            warnings.append(f"Could not load student accounts.\n{e}")

        try:
            self.stats["since"] = self.db.load_stats()
        except OSError:
            pass

        try:
            self.profile_pics.update(self.db.load_profiles())
        except OSError:
            pass

        try:
            self.orders.extend(self.db.load_orders())
        except OSError as e:
            warnings.append(f"Could not load orders.\n{e}")

        try:
            items, images = self.db.load_shop_items()
        except OSError as e:
            warnings.append(f"Could not load shop items.\n{e}")
            items, images = self.db.DEFAULT_SHOP_ITEMS.copy(), {}

        self.shop_items.update(items)
        self.item_images.update(images)
        return warnings

    def save_all(self):
        """Write everything to disk. Returns a list of error messages."""
        errors = []

        for what, func in (
            ("save orders", lambda: self.db.save_orders(self.orders)),
            ("save the student accounts", lambda: self.db.save_students(self.students)),
            ("save shop items",
             lambda: self.db.save_shop_items(self.shop_items, self.item_images)),
            ("save the stats reset", lambda: self.db.save_stats(self.stats["since"])),
            ("save the profile pictures",
             lambda: self.db.save_profiles(self.profile_pics)),
        ):
            try:
                func()
            except OSError as e:
                errors.append(f"Could not {what}.\n{e}")

        return errors


class NoticeService(BaseService):
    """Announcement and maintenance mode."""

    def get_announcement(self):
        """{"date", "text"} or None."""
        found = self.db.load_announcement()
        return {"date": found[0], "text": found[1]} if found else None

    def set_announcement(self, text, actor=BaseService.ADMIN_LABEL):
        text = self.db.clean(text)

        if not text:
            raise ServiceError(
                "Empty Announcement", "Type the announcement first."
            )

        if len(text) > self.NOTE_MAX:
            raise ServiceError(
                "Too Long", f"Keep the announcement under {self.NOTE_MAX} characters."
            )

        try:
            self.db.save_announcement(self._now(), text)
        except OSError as e:
            raise self._file_error("save the announcement", e)

        self.log_activity(actor, "Announcement posted", text)

    def clear_announcement(self, actor=BaseService.ADMIN_LABEL):
        try:
            self.db.save_announcement("", "")
        except OSError as e:
            raise self._file_error("remove the announcement", e)

        self.log_activity(actor, "Announcement removed")

    def get_maintenance(self):
        """{"on": bool, "message": str}"""
        is_on, message = self.db.load_maintenance()
        return {"on": is_on, "message": message}

    def maintenance_message(self):
        return self.get_maintenance()["message"] or (
            "Printing is temporarily paused for maintenance. "
            "Please try again later."
        )

    def set_maintenance(self, is_on, message, actor=BaseService.ADMIN_LABEL):
        message = self.db.clean(message)

        if len(message) > self.NOTE_MAX:
            raise ServiceError(
                "Too Long", f"Keep the message under {self.NOTE_MAX} characters."
            )

        try:
            self.db.save_maintenance(is_on, message)
        except OSError as e:
            raise self._file_error("save the maintenance setting", e)

        self.log_activity(
            actor,
            "Maintenance ON" if is_on else "Maintenance OFF",
            message
        )


class AccountService(BaseService):
    """Logins, registration, passwords and the student profile."""

    def customer_label(self, username):
        info = self.students.get(username)

        if info:
            return f"{info['first']} {info['last']}"

        return username or "N/A"

    def profile_picture(self, student_id):
        """Path of the student's picture, or "" if none (or the file is gone)."""
        path = self.profile_pics.get(student_id, "")
        return path if path and os.path.exists(path) else ""

    def set_profile_picture(self, student_id, source_path):
        if student_id not in self.students:
            raise ServiceError("Not Allowed", "Only students have a profile picture.")

        if not source_path:
            raise ServiceError("No Picture", "Please choose a picture.")

        if os.path.splitext(source_path)[1].lower() not in self.PICTURE_TYPES:
            raise ServiceError(
                "Invalid Picture", "Choose a PNG, JPG, GIF, BMP or WEBP image."
            )

        try:
            if os.path.getsize(source_path) > self.PICTURE_MAX_BYTES:
                raise ServiceError(
                    "Picture Too Large", "Please choose an image under 8 MB."
                )

            stored = self.db.store_file(source_path, self.db.PROFILE_DIR)
        except OSError as e:
            raise self._file_error("save the picture", e)

        old = self.profile_pics.get(student_id, "")
        self.profile_pics[student_id] = stored

        try:
            self.db.save_profiles(self.profile_pics)
        except OSError as e:
            if old:
                self.profile_pics[student_id] = old
            else:
                self.profile_pics.pop(student_id, None)

            self.db.remove_stored_file(stored, self.db.PROFILE_DIR)
            raise self._file_error("save the profile", e)

        if old:
            self.db.remove_stored_file(old, self.db.PROFILE_DIR)

    def change_student_id(self, old_id, new_id, password):
        """A student changes their own ID number. Returns the new ID.

        The ID is the key of the account, so it is also renamed on the
        student's orders and profile picture, and in "remember me".
        """
        new_id = new_id.strip()
        info = self.students.get(old_id)

        if not info:
            raise ServiceError("Not Allowed", "Only students can change their ID.")

        if not new_id or not password:
            raise ServiceError(
                "Missing Information",
                "Enter the new ID number and your current password."
            )

        if not secrets.compare_digest(
            password.encode("utf-8"), info["password"].encode("utf-8")
        ):
            raise ServiceError(
                "Wrong Password", "The password you entered is incorrect."
            )

        if new_id == old_id:
            raise ServiceError("No Change", "That is already your ID number.")

        if not re.fullmatch(r"[A-Za-z0-9-]{3,20}", new_id):
            raise ServiceError(
                "Invalid ID Number",
                "The ID number must be 3-20 characters: letters, numbers "
                "or dashes only."
            )

        if new_id.lower() == self.ADMIN_USERNAME or new_id in self.students:
            raise ServiceError(
                "ID Already Registered", "That ID number is already registered."
            )

        # ---- snapshot, so a failed save can be undone ----
        old_students = dict(self.students)
        old_pictures = dict(self.profile_pics)
        changed_orders = [o for o in self.orders if o.get("username") == old_id]

        # ---- apply (keep the account in the same position in the file) ----
        renamed = {
            (new_id if key == old_id else key): value
            for key, value in self.students.items()
        }
        self.students.clear()
        self.students.update(renamed)

        for order in changed_orders:
            order["username"] = new_id

        if old_id in self.profile_pics:
            self.profile_pics[new_id] = self.profile_pics.pop(old_id)

        try:
            self.db.save_students(self.students)
            self.db.save_orders(self.orders)
            self.db.save_profiles(self.profile_pics)
        except OSError as e:
            self.students.clear()
            self.students.update(old_students)

            for order in changed_orders:
                order["username"] = old_id

            self.profile_pics.clear()
            self.profile_pics.update(old_pictures)

            try:   # put the files back the way they were
                self.db.save_students(self.students)
                self.db.save_orders(self.orders)
                self.db.save_profiles(self.profile_pics)
            except OSError:
                pass

            raise self._file_error("change the ID number", e)

        if self.db.load_remembered() == ("Student", old_id):
            self.db.save_remembered("Student", new_id, True)

        return new_id

    def update_student_info(self, student_id, first, last):
        """A student edits their own first and last name. Returns (first, last).

        Orders are linked by ID number, so they follow the new name automatically.
        """
        first, last = first.strip(), last.strip()
        info = self.students.get(student_id)

        if not info:
            raise ServiceError(
                "Not Allowed", "Only students can edit their information."
            )

        if not first or not last:
            raise ServiceError(
                "Missing Information", "Please enter your first and last name."
            )

        if "|" in first or "|" in last:
            raise ServiceError(
                "Invalid Name", "Names cannot contain the | character."
            )

        if len(first) > 40 or len(last) > 40:
            raise ServiceError(
                "Name Too Long", "Keep each name under 40 characters."
            )

        if first == info["first"] and last == info["last"]:
            raise ServiceError("No Change", "You did not change anything.")

        old_first, old_last = info["first"], info["last"]
        info["first"], info["last"] = first, last

        try:
            self.db.save_students(self.students)
        except OSError as e:
            info["first"], info["last"] = old_first, old_last
            raise self._file_error("save your information", e)

        self.log_activity(
            student_id, "Profile updated",
            f"Name: {old_first} {old_last} -> {first} {last}"
        )
        return first, last

    def remove_profile_picture(self, student_id):
        old = self.profile_pics.pop(student_id, "")

        if not old:
            return

        try:
            self.db.save_profiles(self.profile_pics)
        except OSError as e:
            self.profile_pics[student_id] = old
            raise self._file_error("save the profile", e)

        self.db.remove_stored_file(old, self.db.PROFILE_DIR)

    def get_remembered(self):
        return self.db.load_remembered()

    def set_remembered(self, role, username, keep):
        self.db.save_remembered(role, username, keep)

    def get_theme(self):
        return self.db.load_theme()

    def set_theme(self, mode):
        self.db.save_theme(mode)

    def login_admin(self, username, password):
        return username == self.ADMIN_USERNAME and password == self.ADMIN_PASSWORD

    def login_student(self, student_id, password):
        """Returns the student's info dict, or None if the login is wrong."""
        # re-read students.txt so only saved accounts can log in
        try:
            fresh = self.db.load_students()
            self.students.clear()
            self.students.update(fresh)
        except OSError:
            pass

        info = self.students.get(student_id)

        if not info or not secrets.compare_digest(
            password.encode("utf-8"), info["password"].encode("utf-8")
        ):
            return None

        return info

    def _check_new_password(self, password, confirm):
        if len(password) < 4:
            raise ServiceError(
                "Weak Password", "Password must be at least 4 characters."
            )

        if password != confirm:
            raise ServiceError(
                "Password Mismatch", "The two passwords do not match."
            )

        if "|" in password:
            raise ServiceError(
                "Invalid Password", "Password cannot contain the | character."
            )

    def register_student(self, first, last, student_id, password, confirm):
        first, last, student_id = first.strip(), last.strip(), student_id.strip()

        if not first or not last or not student_id or not password:
            raise ServiceError(
                "Missing Information", "Please fill in all the fields."
            )

        if "|" in first or "|" in last:
            raise ServiceError(
                "Invalid Name", "Names cannot contain the | character."
            )

        if not re.fullmatch(r"[A-Za-z0-9-]{3,20}", student_id):
            raise ServiceError(
                "Invalid ID Number",
                "The ID number must be 3-20 characters: letters, numbers "
                "or dashes only."
            )

        if student_id.lower() == self.ADMIN_USERNAME or student_id in self.students:
            raise ServiceError(
                "ID Already Registered", "That ID number is already registered."
            )

        self._check_new_password(password, confirm)

        self.students[student_id] = {
            "first": first, "last": last, "password": password
        }

        try:
            self.db.save_students(self.students)
        except OSError as e:
            del self.students[student_id]
            raise self._file_error("save the student account", e)

    def reset_password(self, first, last, student_id, password, confirm):
        first, last, student_id = first.strip(), last.strip(), student_id.strip()

        if not first or not last or not student_id or not password:
            raise ServiceError(
                "Missing Information", "Please fill in all the fields."
            )

        info = self.students.get(student_id)

        if (
            not info
            or info["first"].lower() != first.lower()
            or info["last"].lower() != last.lower()
        ):
            raise ServiceError(
                "Verification Failed",
                "The name and ID number do not match a registered student."
            )

        self._check_new_password(password, confirm)

        old_password = info["password"]
        info["password"] = password

        try:
            self.db.save_students(self.students)
        except OSError as e:
            info["password"] = old_password
            raise self._file_error("save the student account", e)


class OrderService(NoticeService):
    """Orders, their status / notes, and the dashboard numbers."""

    def order_details_text(self, order):
        if order["type"] == "Printing Service":
            return (
                f"{order['filename']} | {order['print_type']} | "
                f"{order.get('pages', 1)} pg x {order['copies']} copies"
            )

        return ", ".join(
            f"{item['item']} x {item['quantity']}" for item in order["items"]
        )

    def get_user_orders(self, role, username):
        if role == "Admin":
            return self.orders

        return [o for o in self.orders if o.get("username") == username]

    def counted_orders(self):
        return [o for o in self.orders if o.get("date", "") > self.stats["since"]]

    def dashboard_totals(self):
        counted = self.counted_orders()
        return {
            "total": len(counted),
            "print": sum(1 for o in counted if o["type"] == "Printing Service"),
            "shop": sum(1 for o in counted if o["type"] == "Shop Order"),
            "sales": sum(o["total"] for o in counted),
        }

    def clear_stats(self):
        previous = self.stats["since"]
        self.stats["since"] = self._now()

        try:
            self.db.save_stats(self.stats["since"])
        except OSError as e:
            self.stats["since"] = previous
            raise self._file_error("save the stats reset", e)

        self.log_activity(self.ADMIN_LABEL, "Stats cleared", "Dashboard counters reset")

    def print_total(self, print_type, pages, copies):
        return self.PRINT_PRICES[print_type] * pages * copies

    def create_print_order(self, username, source_path, pages, print_type, copies):
        if self.get_maintenance()["on"]:
            raise ServiceError("Printing Paused", self.maintenance_message())

        if not source_path:
            raise ServiceError(
                "Missing Information", "Please choose a PDF file to print."
            )

        if copies <= 0:
            raise ServiceError("Invalid Copies", "Enter a positive whole number.")

        try:
            stored_pdf = self.db.store_file(source_path, self.db.PDF_DIR)
        except OSError as e:
            raise self._file_error("save the PDF", e)

        order = {
            "username": username,
            "type": "Printing Service",
            "filename": self.db.clean(os.path.basename(source_path)),
            "print_type": print_type,
            "copies": copies,
            "pages": pages,
            "pdf_path": stored_pdf,
            "total": self.print_total(print_type, pages, copies),
            "date": self._now(),
            "status": "Pending",
        }

        self.orders.append(order)

        try:
            self.db.save_orders(self.orders)
        except OSError as e:
            self.orders.remove(order)
            self.db.remove_stored_file(stored_pdf, self.db.PDF_DIR)
            raise self._file_error("save orders", e)

        return order

    def ready_orders(self, username):
        """Orders of this student that can be picked up now."""
        return [
            o for o in self.orders
            if o.get("username") == username and o.get("status") == self.READY_STATUS
        ]

    def set_order_status(self, picked, status, actor=BaseService.ADMIN_LABEL):
        """Change the status of the picked orders (admin)."""
        if status not in self.ORDER_STATUSES:
            raise ServiceError("Invalid Status", "Please choose a valid status.")

        backup = [(order, order.get("status", "Pending")) for order in picked]

        for order in picked:
            order["status"] = status

        try:
            self.db.save_orders(self.orders)
        except OSError as e:
            for order, old in backup:
                order["status"] = old
            raise self._file_error("save orders", e)

        for order, old in backup:
            if old != status:
                self.log_activity(
                    actor, "Status changed",
                    f"{self.order_label(order)}: {old} -> {status}"
                )

    def orders_with_notes(self, username):
        return [
            o for o in self.orders
            if o.get("username") == username and o.get("note")
        ]

    def set_order_note(self, picked, note, actor=BaseService.ADMIN_LABEL):
        """Admin leaves (or clears, with an empty text) a note on orders."""
        note = self.db.clean(note)

        if len(note) > self.NOTE_MAX:
            raise ServiceError(
                "Too Long", f"Keep the note under {self.NOTE_MAX} characters."
            )

        backup = [(order, order.get("note", "")) for order in picked]

        for order in picked:
            if note:
                order["note"] = note
            else:
                order.pop("note", None)

        try:
            self.db.save_orders(self.orders)
        except OSError as e:
            for order, old in backup:
                if old:
                    order["note"] = old
                else:
                    order.pop("note", None)
            raise self._file_error("save orders", e)

        for order in picked:
            self.log_activity(
                actor, "Note added" if note else "Note cleared",
                f"{self.order_label(order)}: {note}" if note else self.order_label(order)
            )

    def delete_orders(self, picked, actor=BaseService.ADMIN_LABEL):
        labels = [self.order_label(o) for o in picked]

        for order in picked:
            self.db.remove_stored_file(order.get("pdf_path", ""), self.db.PDF_DIR)
            self.orders[:] = [o for o in self.orders if o is not order]

        try:
            self.db.save_orders(self.orders)
        except OSError as e:
            raise self._file_error("save orders", e)

        for label in labels:
            self.log_activity(actor, "Order deleted", label)


class ShopService(BaseService):
    """Shopping cart, checkout and shop items."""

    def cart_total(self):
        return sum(item["subtotal"] for item in self.cart)

    def add_to_cart(self, name, quantity_text):
        if name not in self.shop_items:
            raise ServiceError(
                "Unavailable Item", "This item is no longer available."
            )

        try:
            quantity = int(quantity_text)

            if quantity <= 0:
                raise ValueError
        except ValueError:
            raise ServiceError("Invalid Quantity", "Enter a positive whole number.")

        price = self.shop_items[name]
        existing = next((i for i in self.cart if i["item"] == name), None)

        if existing:
            existing["quantity"] += quantity
            existing["price"] = price
            existing["subtotal"] = existing["quantity"] * price
        else:
            self.cart.append({
                "item": name, "quantity": quantity,
                "price": price, "subtotal": price * quantity
            })

        return quantity

    def remove_from_cart(self, name):
        for item in self.cart:
            if item["item"] == name:
                self.cart.remove(item)
                break

    def checkout(self, username):
        if not self.cart:
            raise ServiceError("Empty Cart", "Your shopping cart is empty.")

        order = {
            "username": username,
            "type": "Shop Order",
            "items": [item.copy() for item in self.cart],
            "total": self.cart_total(),
            "date": self._now(),
            "status": "Pending",
        }

        self.orders.append(order)

        try:
            self.db.save_orders(self.orders)
        except OSError as e:
            self.orders.remove(order)
            raise self._file_error("save orders", e)

        self.cart.clear()
        return order

    def save_item(self, old_name, name, price_text, new_picture_source, current_picture):
        """Add a new item (old_name=None) or edit one. Returns (name, price)."""
        name = name.strip()

        if not name:
            raise ServiceError("Invalid Item", "Please enter an item name.")

        if "|" in name:
            raise ServiceError(
                "Invalid Item", "The item name cannot contain the | character."
            )

        try:
            price = float(price_text)

            if not 0 < price < float("inf"):
                raise ValueError
        except ValueError:
            raise ServiceError(
                "Invalid Price", "Enter a valid price greater than zero."
            )

        existing = next(
            (i for i in self.shop_items if i.lower() == name.lower() and i != old_name),
            None
        )

        if existing:
            raise ServiceError(
                "Duplicate Item", f"{existing} already exists in the shop."
            )

        stored_picture = ""

        if new_picture_source:
            try:
                stored_picture = self.db.store_file(new_picture_source, self.db.IMAGE_DIR)
            except OSError as e:
                raise ServiceError("Picture Error", f"Could not save the picture.\n{e}")

        price = round(price, 2)
        backup_items, backup_images = dict(self.shop_items), dict(self.item_images)

        if old_name is not None:
            new_items = {}

            for key, value in self.shop_items.items():
                new_items[name if key == old_name else key] = (
                    price if key == old_name else value
                )

            new_images = {k: v for k, v in self.item_images.items() if k != old_name}
            picture = stored_picture or current_picture

            if picture:
                new_images[name] = picture

            self.shop_items.clear()
            self.shop_items.update(new_items)
            self.item_images.clear()
            self.item_images.update(new_images)
        else:
            self.shop_items[name] = price

            if stored_picture:
                self.item_images[name] = stored_picture

        try:
            self.db.save_shop_items(self.shop_items, self.item_images)
        except OSError as e:
            self.shop_items.clear()
            self.shop_items.update(backup_items)
            self.item_images.clear()
            self.item_images.update(backup_images)
            self.db.remove_stored_file(stored_picture, self.db.IMAGE_DIR)
            raise self._file_error("save shop items", e)

        if old_name is not None:
            if stored_picture:
                self.db.remove_stored_file(current_picture, self.db.IMAGE_DIR)

            # keep cart entries in sync with the edited item
            for entry in self.cart:
                if entry["item"] == old_name:
                    entry["item"] = name
                    entry["price"] = price
                    entry["subtotal"] = price * entry["quantity"]

        if old_name is None:
            self.log_activity(self.ADMIN_LABEL, "Item added", f"{name} at PHP {price:,.2f}")
        else:
            old_price = backup_items.get(old_name, price)

            if round(old_price, 2) != price:
                self.log_activity(
                    self.ADMIN_LABEL, "Price changed",
                    f"{name}: PHP {old_price:,.2f} -> PHP {price:,.2f}"
                )

            if old_name != name:
                self.log_activity(
                    self.ADMIN_LABEL, "Item renamed", f"{old_name} -> {name}"
                )

        return name, price

    def delete_item(self, name):
        old_price = self.shop_items.pop(name)
        old_picture = self.item_images.pop(name, "")

        try:
            self.db.save_shop_items(self.shop_items, self.item_images)
        except OSError as e:
            self.shop_items[name] = old_price

            if old_picture:
                self.item_images[name] = old_picture

            raise self._file_error("save shop items", e)

        self.db.remove_stored_file(old_picture, self.db.IMAGE_DIR)
        self.log_activity(self.ADMIN_LABEL, "Item deleted", f"{name} (PHP {old_price:,.2f})")


class Services(
    AccountService, OrderService, ShopService, NoticeService, BaseService
):
    """The one backend object. Create it once and pass it to the frontend."""