import tkinter as tk
from tkinter import font as tkfont


class Tooltip:
    def __init__(self, widget, text: str, theme=None):
        self.widget = widget
        self.text = text
        self.theme = theme or {}
        self.tipwindow = None
        self._after_id = None
        self.widget.bind("<Enter>", self._schedule_show, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<ButtonPress>", self._hide, add="+")
        self.widget.bind("<Destroy>", self._hide, add="+")

    def set_theme(self, theme):
        self.theme = theme or {}

    def _schedule_show(self, _event=None):
        self._cancel_scheduled_show()
        self._after_id = self.widget.after(350, self._show)

    def _cancel_scheduled_show(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self):
        if self.tipwindow or not self.text:
            return
        self._cancel_scheduled_show()

        try:
            x, y, _cx, cy = self.widget.bbox("insert") or (0, 0, 0, 0)
        except Exception:
            x, y, cy = 0, 0, self.widget.winfo_height()
        x = x + self.widget.winfo_rootx() + 18
        y = y + cy + self.widget.winfo_rooty() + 18
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        try:
            tw.wm_attributes("-topmost", True)
        except Exception:
            pass
        bg = self.theme.get("tooltip_bg", "#1f2937")
        fg = self.theme.get("tooltip_fg", "#f9fafb")
        border = self.theme.get("tooltip_border", "#111827")
        base_font = tkfont.nametofont("TkDefaultFont").copy()
        base_font.configure(size=9)
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background=bg,
            foreground=fg,
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=border,
            padx=8,
            pady=4,
            font=base_font,
            wraplength=320,
        )
        label.pack()

    def _hide(self, _event=None):
        self._cancel_scheduled_show()
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
