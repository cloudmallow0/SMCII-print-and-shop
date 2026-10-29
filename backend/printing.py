import os
import re
import subprocess
import sys
import time

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class PrintService:
    """Everything that touches PDFs and the printer."""

    VIRTUAL_PRINTER_WORDS = (
        "pdf", "onenote", "xps", "fax", "document writer",
        "virtual", "anydesk", "cutepdf", "image writer"
    )

    def count_pdf_pages(self, path):
        """Use pypdf to count the pages of a PDF. Raises on any problem."""
        if PdfReader is None:
            raise RuntimeError(
                "The pypdf library is not installed.\n"
                "Install it with:  pip install pypdf"
            )

        reader = PdfReader(path)

        if reader.is_encrypted and not reader.decrypt(""):
            raise ValueError("This PDF is password-protected.")

        pages = len(reader.pages)

        if pages == 0:
            raise ValueError("This PDF has no pages.")

        return pages

    def open_file(self, path):
        """Open a stored file. Raises FileNotFoundError / OSError."""
        if not path or not os.path.exists(path):
            raise FileNotFoundError(path)

        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def print_file(self, path, copies=1):
        """Send a stored PDF to the default printer. Raises on failure."""
        if not path or not os.path.exists(path):
            raise FileNotFoundError(path)

        if sys.platform.startswith("win"):
            for _ in range(copies):
                os.startfile(path, "print")
                time.sleep(1.5)
        else:  # macOS / Linux (CUPS)
            subprocess.run(["lp", "-n", str(copies), path], check=True)

    @staticmethod
    def _no_window_flags():
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def detect_printer(self):
        """Return {"name", "status"} for the connected physical printer, or None."""
        found = []        # (name, is_default, is_offline)

        try:
            if sys.platform.startswith("win"):
                command = [
                    "powershell", "-NoProfile", "-Command",
                    "Get-CimInstance Win32_Printer | ForEach-Object "
                    "{ '{0}|{1}|{2}|{3}' -f $_.Name,$_.Default,"
                    "$_.WorkOffline,$_.PrinterStatus }"
                ]
                output = subprocess.run(
                    command, capture_output=True, text=True,
                    timeout=12, creationflags=self._no_window_flags()
                ).stdout

                for line in output.splitlines():
                    parts = line.strip().split("|")

                    if len(parts) < 4 or not parts[0]:
                        continue

                    offline = parts[2].lower() == "true" or parts[3] == "7"
                    found.append((parts[0], parts[1].lower() == "true", offline))

            else:
                listing = subprocess.run(
                    ["lpstat", "-p"], capture_output=True, text=True, timeout=8
                ).stdout
                default_out = subprocess.run(
                    ["lpstat", "-d"], capture_output=True, text=True, timeout=8
                ).stdout

                default_name = default_out.split(":")[-1].strip()

                for line in listing.splitlines():
                    match = re.match(r"^printer (\S+) (.*)$", line.strip())

                    if match:
                        found.append((
                            match.group(1),
                            match.group(1) == default_name,
                            "disabled" in match.group(2).lower()
                        ))

        except (OSError, subprocess.SubprocessError):
            return None

        physical = [
            item for item in found
            if not any(word in item[0].lower() for word in self.VIRTUAL_PRINTER_WORDS)
        ]

        if not physical:
            return None

        physical.sort(key=lambda item: (item[2], not item[1]))
        name, _, offline = physical[0]

        if offline:
            return None

        return {"name": name, "status": "Connected"}