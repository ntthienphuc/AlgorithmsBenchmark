import os
import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont

from algorithms import OFFICIAL_ALGORITHM_LABELS
from ui.plot_frame import PlotFrame
from ui.run_frame import RunFrame

THEMES = {
    "light": {
        "bg": "#f4efe7",
        "panel": "#fffaf2",
        "panel_alt": "#efe6d8",
        "text": "#182635",
        "subtle": "#6d7e8d",
        "accent": "#0f8f84",
        "accent_soft": "#d9f3ef",
        "accent_ink": "#0b5e5f",
        "border": "#d7cdbe",
        "plot_bg": "#fffaf2",
        "grid": "#ddd3c5",
        "text_bg": "#fffaf2",
        "text_fg": "#182635",
        "header_bg": "#15344d",
        "header_text": "#f7fbff",
        "header_subtle": "#bfd0dc",
        "accent_text": "#ffffff",
        "danger": "#cf4d5e",
        "danger_soft": "#fde8eb",
        "success": "#2f8f5b",
        "success_soft": "#def5e9",
        "warning": "#b7791f",
        "warning_soft": "#fdf1d9",
        "chip_bg": "#efe6d8",
        "chip_fg": "#33495d",
        "topbar_chip_bg": "#21455f",
        "topbar_chip_fg": "#edf5fb",
        "metric_accent_bg": "#d9f3ef",
        "metric_accent_fg": "#0b5e5f",
        "metric_slate_bg": "#e4edf4",
        "metric_slate_fg": "#284154",
        "metric_success_bg": "#def5e9",
        "metric_success_fg": "#236d47",
        "metric_warm_bg": "#fdf1d9",
        "metric_warm_fg": "#8d5b17",
        "tooltip_bg": "#122230",
        "tooltip_fg": "#f8fafc",
        "tooltip_border": "#0c1721",
        "plot_palette": ["#0f8f84", "#d97706", "#cf4d5e", "#3b82f6", "#2f8f5b", "#8b5cf6", "#0891b2", "#a16207"],
    },
    "dark": {
        "bg": "#0f141a",
        "panel": "#172029",
        "panel_alt": "#1d2933",
        "text": "#e7eff5",
        "subtle": "#9eb1c0",
        "accent": "#5ed1c1",
        "accent_soft": "#173e3c",
        "accent_ink": "#9ef1e3",
        "border": "#2b3946",
        "plot_bg": "#101922",
        "grid": "#31414f",
        "text_bg": "#101921",
        "text_fg": "#e7eff5",
        "header_bg": "#0b151e",
        "header_text": "#eef6fb",
        "header_subtle": "#93a8b8",
        "accent_text": "#062a28",
        "danger": "#ff7d8f",
        "danger_soft": "#38202a",
        "success": "#62d59a",
        "success_soft": "#162e24",
        "warning": "#f2bf66",
        "warning_soft": "#3a2a13",
        "chip_bg": "#1f2b35",
        "chip_fg": "#c9d8e4",
        "topbar_chip_bg": "#143e56",
        "topbar_chip_fg": "#e7f7ff",
        "metric_accent_bg": "#173e3c",
        "metric_accent_fg": "#9ef1e3",
        "metric_slate_bg": "#22313d",
        "metric_slate_fg": "#d2dfeb",
        "metric_success_bg": "#162e24",
        "metric_success_fg": "#86ebb4",
        "metric_warm_bg": "#3a2a13",
        "metric_warm_fg": "#ffd589",
        "tooltip_bg": "#0d141b",
        "tooltip_fg": "#e2e8f0",
        "tooltip_border": "#21303b",
        "plot_palette": ["#5ed1c1", "#f2bf66", "#ff7d8f", "#60a5fa", "#62d59a", "#a78bfa", "#38bdf8", "#f59e0b"],
    },
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.option_add("*tearOff", False)
        self._init_fonts()
        self.title("Partition Benchmark Studio")
        self.geometry("1120x760")
        self.minsize(980, 680)

        self.var_outdir = tk.StringVar(value=os.path.join(os.getcwd(), "outputs"))
        self.var_dark = tk.BooleanVar(value=False)

        topbar = ttk.Frame(self, padding=(16, 12), style="Topbar.TFrame")
        topbar.pack(fill="x")
        title_block = ttk.Frame(topbar, style="Topbar.TFrame")
        title_block.pack(side="left")
        ttk.Label(title_block, text="Phân hoạch các số", style="Topbar.Title.TLabel").pack(anchor="w")
        ttk.Label(
            title_block,
            text=f"{len(OFFICIAL_ALGORITHM_LABELS)} chiến lược học thuật chính thức | benchmark trên cùng base array",
            style="Topbar.Sub.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        right_block = ttk.Frame(topbar, style="Topbar.TFrame")
        right_block.pack(side="right")
        ttk.Checkbutton(
            right_block,
            text="Chế độ tối",
            variable=self.var_dark,
            command=self._toggle_theme,
            style="Topbar.TCheckbutton",
        ).pack(side="right")
        badges = ttk.Frame(right_block, style="Topbar.TFrame")
        badges.pack(side="right", padx=(0, 16))
        ttk.Label(badges, text="Fair benchmark", style="Topbar.Badge.TLabel").pack(side="left")
        ttk.Label(badges, text="Hover plot", style="Topbar.BadgeAlt.TLabel").pack(side="left", padx=(8, 0))

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=14, pady=14)

        self.plot_tab = PlotFrame(nb, self.var_outdir)
        self.run_tab = RunFrame(nb, self.var_outdir, self.plot_tab)

        nb.add(self.run_tab, text="Chạy test")
        nb.add(self.plot_tab, text="Plot lịch sử")

        self._apply_theme("light")
        self.plot_tab.refresh()

    def _init_fonts(self):
        base_family = self._pick_font(
            ["Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", "Noto Sans", "Roboto", "Tahoma", "Arial"],
            "TkDefaultFont",
        )
        heading_family = self._pick_font(
            ["Segoe UI Variable Display", "Segoe UI Semibold", "Segoe UI", "Noto Sans", "Roboto", "Tahoma", "Arial"],
            base_family,
        )
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=base_family, size=10)
        heading_font = tkfont.nametofont("TkHeadingFont")
        heading_font.configure(family=heading_family, size=11, weight="bold")
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family=base_family, size=10)
        self._font_title = tkfont.Font(family=heading_family, size=17, weight="bold")
        self._font_header = tkfont.Font(family=heading_family, size=13, weight="bold")
        self._font_section = tkfont.Font(family=heading_family, size=12, weight="bold")
        self._font_body = tkfont.Font(family=base_family, size=10)
        self._font_small = tkfont.Font(family=base_family, size=9)
        self._font_table_header = tkfont.Font(family=heading_family, size=9, weight="bold")
        self._font_card_label = tkfont.Font(family=heading_family, size=10, weight="bold")
        self._font_metric_value = tkfont.Font(family=heading_family, size=16, weight="bold")
        self._font_chip = tkfont.Font(family=heading_family, size=8, weight="bold")
        mono_family = self._pick_font(["Cascadia Code", "Consolas", "JetBrains Mono", "Courier New"], "TkFixedFont")
        fixed_font = tkfont.nametofont("TkFixedFont")
        fixed_font.configure(family=mono_family, size=10)

    @staticmethod
    def _pick_font(candidates, fallback):
        try:
            available = set(tkfont.families())
        except Exception:
            return fallback
        for name in candidates:
            if name in available:
                return name
        return fallback

    def _toggle_theme(self):
        theme_name = "dark" if self.var_dark.get() else "light"
        self._apply_theme(theme_name)

    def _apply_theme(self, theme_name: str):
        theme = THEMES[theme_name]
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.configure(background=theme["bg"])
        style.configure("TFrame", background=theme["bg"])
        style.configure("TLabel", background=theme["bg"], foreground=theme["text"])
        style.configure("Subtle.TLabel", background=theme["bg"], foreground=theme["subtle"])
        style.configure("PanelSubtle.TLabel", background=theme["panel"], foreground=theme["subtle"], font=self._font_small)
        style.configure("Header.TLabel", font=self._font_header, foreground=theme["text"], background=theme["bg"])
        style.configure("SubHeader.TLabel", font=self._font_body, foreground=theme["subtle"], background=theme["bg"])
        style.configure("Info.TLabel", font=self._font_body, foreground=theme["text"], background=theme["panel"])
        style.configure("Topbar.TFrame", background=theme["header_bg"])
        style.configure("Topbar.Title.TLabel", font=self._font_title, foreground=theme["header_text"], background=theme["header_bg"])
        style.configure("Topbar.Sub.TLabel", font=self._font_body, foreground=theme["header_subtle"], background=theme["header_bg"])
        style.configure("Topbar.TCheckbutton", background=theme["header_bg"], foreground=theme["header_text"], font=self._font_body)
        style.map("Topbar.TCheckbutton", background=[("active", theme["header_bg"])], foreground=[("active", theme["header_text"])])
        style.configure("Topbar.Badge.TLabel", background=theme["topbar_chip_bg"], foreground=theme["topbar_chip_fg"], font=self._font_chip, padding=(10, 4))
        style.configure("Topbar.BadgeAlt.TLabel", background=theme["accent"], foreground=theme["accent_text"], font=self._font_chip, padding=(10, 4))
        style.configure("Hero.TFrame", background=theme["panel_alt"])
        style.configure("Hero.Title.TLabel", font=self._font_section, foreground=theme["text"], background=theme["panel_alt"])
        style.configure("Hero.Sub.TLabel", font=self._font_small, foreground=theme["subtle"], background=theme["panel_alt"])
        style.configure("Section.TFrame", background=theme["panel_alt"])
        style.configure("Section.Title.TLabel", font=self._font_section, foreground=theme["text"], background=theme["panel_alt"])
        style.configure("Section.Sub.TLabel", font=self._font_small, foreground=theme["subtle"], background=theme["panel_alt"])
        style.configure("TLabelframe", background=theme["bg"], foreground=theme["text"], bordercolor=theme["border"])
        style.configure("TLabelframe.Label", background=theme["bg"], foreground=theme["text"], font=self._font_card_label)
        style.configure("Card.TLabelframe", background=theme["panel"], foreground=theme["text"], bordercolor=theme["border"])
        style.configure("Card.TLabelframe.Label", background=theme["panel"], foreground=theme["text"], font=self._font_card_label)
        style.configure("TNotebook", background=theme["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))
        style.configure("TNotebook.Tab", padding=(18, 10), font=self._font_body, background=theme["panel_alt"], foreground=theme["subtle"])
        style.map(
            "TNotebook.Tab",
            background=[("selected", theme["panel"]), ("active", theme["accent_soft"])],
            foreground=[("selected", theme["text"]), ("active", theme["text"])],
        )
        style.configure("TEntry", fieldbackground=theme["panel"], foreground=theme["text"], bordercolor=theme["border"], padding=6)
        style.configure("TCombobox", fieldbackground=theme["panel"], foreground=theme["text"], bordercolor=theme["border"], padding=4)
        style.configure("TCheckbutton", background=theme["bg"], foreground=theme["text"], font=self._font_body)
        style.map("TCheckbutton", background=[("active", theme["bg"])], foreground=[("active", theme["text"])])
        style.configure("TButton", padding=(12, 8), background=theme["panel_alt"], foreground=theme["text"], font=self._font_body, bordercolor=theme["border"])
        style.map("TButton", background=[("active", theme["accent_soft"])], foreground=[("active", theme["text"])])
        style.configure("Accent.TButton", background=theme["accent"], foreground=theme["accent_text"], padding=(14, 8), font=self._font_card_label, bordercolor=theme["accent"])
        style.map("Accent.TButton", background=[("active", theme["accent"])], foreground=[("active", theme["accent_text"])])
        style.configure("Danger.TButton", background=theme["danger"], foreground="#ffffff", padding=(12, 8), font=self._font_body, bordercolor=theme["danger"])
        style.map("Danger.TButton", background=[("active", theme["danger"])], foreground=[("active", "#ffffff")])
        style.configure(
            "Summary.Treeview",
            background=theme["panel"],
            fieldbackground=theme["panel"],
            foreground=theme["text"],
            rowheight=30,
        )
        style.configure(
            "Summary.Treeview.Heading",
            background=theme["panel_alt"],
            foreground=theme["text"],
            font=self._font_table_header,
        )
        style.map("Summary.Treeview", background=[("selected", theme["accent"])], foreground=[("selected", "#ffffff")])
        style.configure("Chip.TLabel", background=theme["chip_bg"], foreground=theme["chip_fg"], font=self._font_chip, padding=(10, 4))
        style.configure("ChipAccent.TLabel", background=theme["accent_soft"], foreground=theme["accent_ink"], font=self._font_chip, padding=(10, 4))
        style.configure("AccentSubtleChip.TLabel", background=theme["metric_accent_bg"], foreground=theme["metric_accent_fg"], font=self._font_chip, padding=(10, 4))
        style.configure("SlateChip.TLabel", background=theme["metric_slate_bg"], foreground=theme["metric_slate_fg"], font=self._font_chip, padding=(10, 4))
        style.configure("SuccessChip.TLabel", background=theme["success_soft"], foreground=theme["success"], font=self._font_chip, padding=(10, 4))
        style.configure("DangerChip.TLabel", background=theme["danger_soft"], foreground=theme["danger"], font=self._font_chip, padding=(10, 4))
        style.configure("WarmChip.TLabel", background=theme["warning_soft"], foreground=theme["warning"], font=self._font_chip, padding=(10, 4))
        style.configure("Metric.TFrame", background=theme["metric_accent_bg"])
        style.configure("MetricAlt.TFrame", background=theme["metric_slate_bg"])
        style.configure("MetricWarm.TFrame", background=theme["metric_warm_bg"])
        style.configure("MetricSuccess.TFrame", background=theme["metric_success_bg"])
        style.configure("Metric.Label.TLabel", background=theme["metric_accent_bg"], foreground=theme["metric_accent_fg"], font=self._font_small)
        style.configure("MetricAlt.Label.TLabel", background=theme["metric_slate_bg"], foreground=theme["metric_slate_fg"], font=self._font_small)
        style.configure("MetricWarm.Label.TLabel", background=theme["metric_warm_bg"], foreground=theme["metric_warm_fg"], font=self._font_small)
        style.configure("MetricSuccess.Label.TLabel", background=theme["metric_success_bg"], foreground=theme["metric_success_fg"], font=self._font_small)
        style.configure("Metric.Value.TLabel", background=theme["metric_accent_bg"], foreground=theme["metric_accent_fg"], font=self._font_metric_value)
        style.configure("MetricAlt.Value.TLabel", background=theme["metric_slate_bg"], foreground=theme["metric_slate_fg"], font=self._font_metric_value)
        style.configure("MetricWarm.Value.TLabel", background=theme["metric_warm_bg"], foreground=theme["metric_warm_fg"], font=self._font_metric_value)
        style.configure("MetricSuccess.Value.TLabel", background=theme["metric_success_bg"], foreground=theme["metric_success_fg"], font=self._font_metric_value)
        style.configure("Metric.Help.TLabel", background=theme["metric_accent_bg"], foreground=theme["metric_accent_fg"], font=self._font_small)
        style.configure("MetricAlt.Help.TLabel", background=theme["metric_slate_bg"], foreground=theme["metric_slate_fg"], font=self._font_small)
        style.configure("MetricWarm.Help.TLabel", background=theme["metric_warm_bg"], foreground=theme["metric_warm_fg"], font=self._font_small)
        style.configure("MetricSuccess.Help.TLabel", background=theme["metric_success_bg"], foreground=theme["metric_success_fg"], font=self._font_small)
        style.configure("Success.TLabel", background=theme["success_soft"], foreground=theme["success"], font=self._font_small)
        style.configure("Warning.TLabel", background=theme["warning_soft"], foreground=theme["warning"], font=self._font_small)

        self.plot_tab.apply_theme(theme)
        self.run_tab.apply_theme(theme)


def main():
    try:
        app = App()
        app.mainloop()
    except tk.TclError as exc:
        raise SystemExit(
            "Khong khoi tao duoc giao dien Tkinter. Hay kiem tra cai dat Tcl/Tk cua Python dang su dung.\n"
            f"Chi tiet: {exc}"
        ) from exc


if __name__ == "__main__":
    main()
