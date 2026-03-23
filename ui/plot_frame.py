import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from algorithms import OFFICIAL_ALGORITHM_LABELS
from history.persistence import load_history, make_dataset_key

PLOT_SCOPE_DATASET = "Gộp theo dataset"
PLOT_SCOPE_BATCH = "Chỉ 1 batch"
PLOT_SERIES_STYLES = {
    "Direct Scan": {"color": "#7c3aed"},
    "Two Pointers": {"color": "#e11d48"},
    "Transform-and-Conquer": {"color": "#0284c7"},
    "Divide-and-Conquer": {"color": "#f59e0b"},
}


class PlotFrame(ttk.Frame):
    def __init__(self, master, outdir_var: tk.StringVar):
        super().__init__(master)
        self.outdir_var = outdir_var
        self._theme = None
        self._series_lookup = []
        self._hover_annotation = None
        self._legend_artist_map = {}
        self._legend_entry_map = {}
        self._last_history = []
        self._dataset_options = {}
        self._batch_options = {}
        self._preferred_dataset_key = None
        self._preferred_batch_id = None

        self.var_log_scale = tk.BooleanVar(value=False)
        self.var_scope = tk.StringVar(value=PLOT_SCOPE_DATASET)
        self.var_dataset = tk.StringVar(value="")
        self.var_batch = tk.StringVar(value="")
        self.dataset_note = tk.StringVar(value="Plot chỉ gộp các mẫu cùng seed và cùng tỷ lệ âm.")
        self.metric_selected = tk.StringVar(value="0")
        self.metric_samples = tk.StringVar(value="0")
        self.metric_best = tk.StringVar(value="--")
        self.metric_scale = tk.StringVar(value="Linear")
        self.metric_best_note = tk.StringVar(value="Chưa có dữ liệu hợp lệ.")
        self.metric_scale_note = tk.StringVar(value="Trục Y tuyến tính.")

        self.scroll_canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.scroll_canvas.yview)
        self.scrollbar_y.pack(side="right", fill="y")
        self.scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.scroll_canvas.xview)
        self.scrollbar_x.pack(side="bottom", fill="x")
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set)

        self.content = ttk.Frame(self.scroll_canvas)
        self._canvas_window = self.scroll_canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_configure)
        self.scroll_canvas.bind("<Configure>", self._on_canvas_configure)

        controls = ttk.Frame(self.content, padding=(14, 12), style="Hero.TFrame")
        controls.pack(fill="x")
        title_block = ttk.Frame(controls, style="Hero.TFrame")
        title_block.pack(side="left")
        ttk.Label(
            title_block,
            text="Biểu đồ lịch sử runtime trung bình theo kích thước test",
            style="Hero.Title.TLabel",
        ).pack(anchor="w")
        ttk.Label(title_block, text="Multi-select | hover value | click legend để ẩn/hiện", style="Hero.Sub.TLabel").pack(anchor="w", pady=(2, 0))

        right_block = ttk.Frame(controls, style="Hero.TFrame")
        right_block.pack(side="right")
        ttk.Button(right_block, text="Xuất PNG", command=self.export_png).pack(side="right")
        ttk.Button(right_block, text="Làm mới biểu đồ", command=self.refresh, style="Accent.TButton").pack(side="right", padx=8)
        ttk.Button(right_block, text="Xóa biểu đồ", command=self.clear_plot).pack(side="right")
        ttk.Button(
            right_block,
            text="Xóa lịch sử (results.csv)",
            command=self.delete_history,
            style="Danger.TButton",
        ).pack(side="right", padx=8)

        chip_bar = ttk.Frame(right_block, style="Hero.TFrame")
        chip_bar.pack(side="right", padx=(0, 16))
        ttk.Label(chip_bar, text="Hover", style="Chip.TLabel").pack(side="left")
        ttk.Label(chip_bar, text="Legend toggle", style="ChipAccent.TLabel").pack(side="left", padx=(8, 0))

        self.lbl = ttk.Label(self.content, text="", style="Section.Sub.TLabel")
        self.lbl.pack(fill="x", padx=10, pady=(4, 0))

        top_grid = ttk.Frame(self.content, padding=(6, 6, 6, 0))
        top_grid.pack(fill="x")
        top_grid.columnconfigure(0, weight=3)
        top_grid.columnconfigure(1, weight=2)

        left_stack = ttk.Frame(top_grid)
        left_stack.grid(row=0, column=0, sticky="nsew")
        right_stack = ttk.Frame(top_grid)
        right_stack.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        context = ttk.LabelFrame(left_stack, text="Dataset / batch", padding=(10, 8), style="Card.TLabelframe")
        context.pack(fill="x")

        context_row = ttk.Frame(context)
        context_row.pack(fill="x")
        ttk.Label(context_row, text="Dataset:").pack(side="left")
        self.cmb_dataset = ttk.Combobox(context_row, textvariable=self.var_dataset, state="readonly", width=42)
        self.cmb_dataset.pack(side="left", padx=6)
        self.cmb_dataset.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(context_row, text="Phạm vi:").pack(side="left", padx=(16, 0))
        self.cmb_scope = ttk.Combobox(
            context_row,
            textvariable=self.var_scope,
            values=(PLOT_SCOPE_DATASET, PLOT_SCOPE_BATCH),
            state="readonly",
            width=18,
        )
        self.cmb_scope.pack(side="left", padx=6)
        self.cmb_scope.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(context_row, text="Batch:").pack(side="left", padx=(16, 0))
        self.cmb_batch = ttk.Combobox(context_row, textvariable=self.var_batch, state="disabled", width=28)
        self.cmb_batch.pack(side="left", padx=6)
        self.cmb_batch.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Button(context_row, text="Mới nhất", command=self._select_latest_dataset).pack(side="right")
        ttk.Label(context, textvariable=self.dataset_note, style="Subtle.TLabel", wraplength=1200).pack(anchor="w", pady=(6, 0))

        metrics = ttk.LabelFrame(right_stack, text="Snapshot", padding=(10, 8), style="Card.TLabelframe")
        metrics.pack(fill="both")
        metric_row1 = ttk.Frame(metrics)
        metric_row1.pack(fill="x")
        self._build_metric_card(metric_row1, "Metric.TFrame", "Metric.Label.TLabel", "Metric.Value.TLabel", "Metric.Help.TLabel", "Đang chọn", self.metric_selected, "Số thuật toán đang được hiển thị").pack(side="left", fill="x", expand=True)
        self._build_metric_card(metric_row1, "MetricAlt.TFrame", "MetricAlt.Label.TLabel", "MetricAlt.Value.TLabel", "MetricAlt.Help.TLabel", "Mẫu hợp lệ", self.metric_samples, "Số bản ghi OK được dùng để vẽ").pack(side="left", fill="x", expand=True, padx=(8, 0))
        metric_row2 = ttk.Frame(metrics)
        metric_row2.pack(fill="x", pady=(8, 0))
        self._build_metric_card(metric_row2, "MetricSuccess.TFrame", "MetricSuccess.Label.TLabel", "MetricSuccess.Value.TLabel", "MetricSuccess.Help.TLabel", "Nhanh nhất", self.metric_best, self.metric_best_note).pack(side="left", fill="x", expand=True)
        self._build_metric_card(metric_row2, "MetricWarm.TFrame", "MetricWarm.Label.TLabel", "MetricWarm.Value.TLabel", "MetricWarm.Help.TLabel", "Scale", self.metric_scale, self.metric_scale_note).pack(side="left", fill="x", expand=True, padx=(8, 0))

        filters = ttk.LabelFrame(left_stack, text="Bộ lọc thuật toán", padding=(10, 8), style="Card.TLabelframe")
        filters.pack(fill="x", pady=(10, 0))

        quick_filters = ttk.Frame(filters)
        quick_filters.pack(fill="x")
        ttk.Label(quick_filters, text="Chọn nhanh:").pack(side="left")
        ttk.Button(quick_filters, text="Tất cả", command=lambda: self._set_filter_state(True)).pack(side="left", padx=(8, 4))
        ttk.Button(quick_filters, text="Bỏ chọn hết", command=lambda: self._set_filter_state(False)).pack(side="left")
        ttk.Button(quick_filters, text="Chỉ có dữ liệu", command=self._select_algorithms_with_data).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(quick_filters, text="Log scale Y", variable=self.var_log_scale, command=self.refresh).pack(side="right")

        self.filter_vars = {alg: tk.BooleanVar(value=True) for alg in OFFICIAL_ALGORITHM_LABELS}
        filter_grid = ttk.Frame(filters)
        filter_grid.pack(fill="x", pady=(8, 0))
        for idx, alg in enumerate(OFFICIAL_ALGORITHM_LABELS):
            chk = ttk.Checkbutton(
                filter_grid,
                text=alg,
                variable=self.filter_vars[alg],
                command=self.refresh,
            )
            chk.grid(row=idx // 3, column=idx % 3, sticky="w", padx=(0, 18), pady=2)

        plot_card = ttk.LabelFrame(self.content, text="Biểu đồ", padding=(10, 8), style="Card.TLabelframe")
        plot_card.pack(fill="both", expand=True, padx=6, pady=(10, 6))
        plot_host = ttk.Frame(plot_card)
        plot_host.pack(fill="both", expand=True)
        plot_host.configure(height=560)
        plot_host.pack_propagate(False)

        self.fig = Figure(figsize=(10.2, 5.8), dpi=100, constrained_layout=True)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_host)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=6, pady=6)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("figure_leave_event", self._hide_hover_annotation)
        self.canvas.mpl_connect("pick_event", self._on_pick)

        self.toolbar = NavigationToolbar2Tk(self.canvas, plot_card)
        self.toolbar.update()

        try:
            self.outdir_var.trace_add("write", lambda *_: self.refresh())
        except Exception:
            pass

        self._install_scroll_bindings()
        self._apply_axis_style()
        self._draw_empty_plot("Chưa có dữ liệu benchmark.")

    @staticmethod
    def _build_metric_card(parent, frame_style, label_style, value_style, help_style, title, variable, help_text_var):
        card = ttk.Frame(parent, padding=(12, 10), style=frame_style)
        ttk.Label(card, text=title, style=label_style).pack(anchor="w")
        ttk.Label(card, textvariable=variable, style=value_style).pack(anchor="w", pady=(4, 0))
        if isinstance(help_text_var, tk.Variable):
            ttk.Label(card, textvariable=help_text_var, style=help_style, wraplength=200, justify="left").pack(anchor="w", pady=(4, 0))
        else:
            ttk.Label(card, text=help_text_var, style=help_style, wraplength=200, justify="left").pack(anchor="w", pady=(4, 0))
        return card

    def _on_content_configure(self, _event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))
        requested_width = self.content.winfo_reqwidth()
        canvas_width = self.scroll_canvas.winfo_width()
        self.scroll_canvas.itemconfigure(self._canvas_window, width=max(requested_width, canvas_width))

    def _on_canvas_configure(self, _event):
        self._on_content_configure()

    def _install_scroll_bindings(self):
        self._bind_mousewheel_descendants(self.scroll_canvas, self._on_vertical_mousewheel, self._on_horizontal_mousewheel)
        self.scrollbar_y.bind("<MouseWheel>", self._on_vertical_mousewheel, add="+")
        self.scrollbar_y.bind("<Shift-MouseWheel>", self._on_vertical_mousewheel, add="+")
        self.scrollbar_x.bind("<MouseWheel>", self._on_horizontal_mousewheel, add="+")
        self.scrollbar_x.bind("<Shift-MouseWheel>", self._on_horizontal_mousewheel, add="+")

    def _bind_mousewheel_descendants(self, widget, vertical_handler, horizontal_handler=None):
        widget.bind("<MouseWheel>", vertical_handler, add="+")
        if horizontal_handler is not None:
            widget.bind("<Shift-MouseWheel>", horizontal_handler, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_descendants(child, vertical_handler, horizontal_handler)

    @staticmethod
    def _wheel_steps(event):
        delta = getattr(event, "delta", 0)
        if delta == 0:
            return 0
        steps = int(-delta / 120)
        if steps == 0:
            return -1 if delta > 0 else 1
        return steps

    @staticmethod
    def _can_scroll(widget, axis: str):
        start, end = getattr(widget, f"{axis}view")()
        return not (start == 0.0 and end == 1.0)

    def _on_vertical_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0 or not self._can_scroll(self.scroll_canvas, "y"):
            return "break"
        self.scroll_canvas.yview_scroll(steps, "units")
        return "break"

    def _on_horizontal_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0 or not self._can_scroll(self.scroll_canvas, "x"):
            return "break"
        self.scroll_canvas.xview_scroll(steps, "units")
        return "break"

    def apply_theme(self, theme):
        self._theme = theme
        plot_bg = theme["plot_bg"]
        self.scroll_canvas.configure(background=theme["bg"])
        self.fig.patch.set_facecolor(plot_bg)
        self.canvas.get_tk_widget().configure(
            background=plot_bg,
            highlightthickness=1,
            highlightbackground=theme["border"],
        )
        self._style_toolbar(theme)
        self._apply_axis_style()
        self.canvas.draw_idle()

    def _style_toolbar(self, theme):
        try:
            self.toolbar.configure(background=theme["panel"])
        except Exception:
            return
        for child in self.toolbar.winfo_children():
            try:
                child.configure(background=theme["panel"], foreground=theme["text"])
            except Exception:
                continue

    def _apply_axis_style(self):
        theme = self._theme or {
            "text": "#0f172a",
            "grid": "#e2e8f0",
            "plot_bg": "#ffffff",
        }
        plot_bg = theme["plot_bg"]
        axis_bg = theme.get("panel_alt", plot_bg)
        text_color = theme["text"]
        grid_color = theme["grid"]
        palette = theme.get("plot_palette")

        self.ax.set_xlabel("Kích thước test (n)")
        self.ax.set_ylabel("Runtime trung bình (μs)")
        self.ax.set_title("Lịch sử benchmark các thuật toán chính")
        self.ax.set_facecolor(axis_bg)
        self.ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        self.ax.set_yscale("log" if self.var_log_scale.get() else "linear")
        if palette:
            self.ax.set_prop_cycle(color=palette)
        self.ax.title.set_color(text_color)
        self.ax.xaxis.label.set_color(text_color)
        self.ax.yaxis.label.set_color(text_color)
        self.ax.tick_params(colors=text_color)
        for spine in self.ax.spines.values():
            spine.set_color(grid_color)
        self.ax.grid(True, linewidth=0.45, color=grid_color)

    def _build_hover_annotation(self):
        theme = self._theme or {"panel": "#ffffff", "grid": "#e2e8f0", "text": "#0f172a"}
        self._hover_annotation = self.ax.annotate(
            "",
            xy=(0, 0),
            xytext=(12, 12),
            textcoords="offset points",
            ha="left",
            va="bottom",
            color=theme["text"],
            bbox={
                "boxstyle": "round,pad=0.35",
                "fc": theme["panel"],
                "ec": theme["grid"],
                "alpha": 0.96,
            },
        )
        self._hover_annotation.set_visible(False)

    def _position_hover_annotation(self, idx: int, series_size: int, x_value, y_value):
        if not self._hover_annotation:
            return
        canvas_width = max(1, self.canvas.get_tk_widget().winfo_width())
        canvas_height = max(1, self.canvas.get_tk_widget().winfo_height())
        display_x, display_y = self.ax.transData.transform((x_value, y_value))

        near_right_edge = display_x >= canvas_width - 170
        near_top_edge = display_y >= canvas_height - 100

        offset_x = -12 if idx >= series_size - 1 or near_right_edge else 12
        offset_y = -12 if near_top_edge else 12

        self._hover_annotation.set_ha("right" if offset_x < 0 else "left")
        self._hover_annotation.set_va("top" if offset_y < 0 else "bottom")
        self._hover_annotation.xyann = (offset_x, offset_y)

    def _selected_algorithms(self):
        return [alg for alg in OFFICIAL_ALGORITHM_LABELS if self.filter_vars[alg].get()]

    def _series_style(self, algorithm: str):
        base = PLOT_SERIES_STYLES.get(algorithm, {})
        return {
            "color": base.get("color"),
            "marker": "o",
            "linewidth": 2.4,
            "markersize": 5.8,
        }

    @staticmethod
    def _format_timestamp(timestamp: str):
        ts = (timestamp or "").strip()
        if len(ts) >= 15 and ts[8] == "_" and ts[15] == "_":
            return f"{ts[6:8]}/{ts[4:6]}/{ts[0:4]} {ts[9:11]}:{ts[11:13]}:{ts[13:15]}"
        return ts or "--"

    @staticmethod
    def _dataset_display(group):
        return (
            f"seed={group['seed']} | ratio={group['neg_ratio']:.3f} | "
            f"{len(group['ns'])} n | {group['ok_count']} mẫu OK"
        )

    def _batch_display(self, group):
        return (
            f"{group['run_kind']} | {self._format_timestamp(group['latest_ts'])} | "
            f"{len(group['ns'])} n | {group['ok_count']} mẫu OK"
        )

    def _summarize_datasets(self, history):
        groups = {}
        for record in history:
            key = record["dataset_key"]
            group = groups.setdefault(
                key,
                {
                    "key": key,
                    "seed": record["seed"],
                    "neg_ratio": record["neg_ratio"],
                    "total_count": 0,
                    "ok_count": 0,
                    "ns": set(),
                    "batch_ids": set(),
                    "latest_ts": "",
                },
            )
            group["total_count"] += 1
            if record["ok"]:
                group["ok_count"] += 1
            group["ns"].add(record["n"])
            group["batch_ids"].add(record["batch_id"])
            if record["timestamp"] > group["latest_ts"]:
                group["latest_ts"] = record["timestamp"]
        return groups

    def _summarize_batches(self, records):
        groups = {}
        for record in records:
            batch_id = record["batch_id"]
            group = groups.setdefault(
                batch_id,
                {
                    "batch_id": batch_id,
                    "run_kind": record["run_kind"] or "single",
                    "total_count": 0,
                    "ok_count": 0,
                    "ns": set(),
                    "latest_ts": "",
                },
            )
            group["total_count"] += 1
            if record["ok"]:
                group["ok_count"] += 1
            group["ns"].add(record["n"])
            if record["timestamp"] > group["latest_ts"]:
                group["latest_ts"] = record["timestamp"]
        return groups

    def _current_dataset_key(self):
        return self._dataset_options.get(self.var_dataset.get().strip())

    def _current_batch_id(self):
        return self._batch_options.get(self.var_batch.get().strip())

    def _select_latest_dataset(self):
        self._preferred_dataset_key = None
        self._preferred_batch_id = None
        self.var_dataset.set("")
        self.var_batch.set("")
        self.refresh()

    def focus_dataset(self, seed: int, neg_ratio: float, batch_id=None, refresh: bool = True):
        self._preferred_dataset_key = make_dataset_key(seed, neg_ratio)
        self._preferred_batch_id = batch_id or None
        if refresh:
            self.refresh()

    def _sync_dataset_controls(self, dataset_groups):
        ordered = sorted(dataset_groups.values(), key=lambda group: group["latest_ts"], reverse=True)
        self._dataset_options = {self._dataset_display(group): group["key"] for group in ordered}
        values = list(self._dataset_options)
        self.cmb_dataset.configure(values=values, state="readonly" if values else "disabled")

        target_key = self._current_dataset_key()
        if target_key not in dataset_groups:
            target_key = self._preferred_dataset_key
        if target_key not in dataset_groups and ordered:
            target_key = ordered[0]["key"]

        if target_key in dataset_groups:
            for label, key in self._dataset_options.items():
                if key == target_key:
                    self.var_dataset.set(label)
                    self._preferred_dataset_key = target_key
                    break
        else:
            self.var_dataset.set("")

        return ordered

    def _sync_batch_controls(self, batch_groups):
        ordered = sorted(batch_groups.values(), key=lambda group: group["latest_ts"], reverse=True)
        self._batch_options = {self._batch_display(group): group["batch_id"] for group in ordered}
        values = list(self._batch_options)

        batch_state = "readonly" if values and self.var_scope.get() == PLOT_SCOPE_BATCH else "disabled"
        self.cmb_batch.configure(values=values, state=batch_state)

        target_batch = self._current_batch_id()
        if target_batch not in batch_groups:
            target_batch = self._preferred_batch_id
        if target_batch not in batch_groups and ordered:
            target_batch = ordered[0]["batch_id"]

        if target_batch in batch_groups:
            for label, batch_id in self._batch_options.items():
                if batch_id == target_batch:
                    self.var_batch.set(label)
                    self._preferred_batch_id = target_batch
                    break
        else:
            self.var_batch.set("")

        return ordered

    def _set_filter_state(self, value: bool):
        for var in self.filter_vars.values():
            var.set(value)
        self.refresh()

    def _select_algorithms_with_data(self):
        if not self._last_history:
            self.refresh()
        records = list(self._last_history)
        dataset_key = self._current_dataset_key()
        if dataset_key:
            records = [record for record in records if record["dataset_key"] == dataset_key]

        if self.var_scope.get() == PLOT_SCOPE_BATCH:
            batch_id = self._current_batch_id()
            if batch_id:
                records = [record for record in records if record["batch_id"] == batch_id]

        available = {record["algorithm"] for record in records if record["ok"]}
        for alg, var in self.filter_vars.items():
            var.set(alg in available)
        self.refresh()

    def _hide_hover_annotation(self, _event=None):
        if self._hover_annotation and self._hover_annotation.get_visible():
            self._hover_annotation.set_visible(False)
            self.canvas.draw_idle()

    def _on_hover(self, event):
        if event.inaxes != self.ax or not self._series_lookup or not self._hover_annotation:
            self._hide_hover_annotation()
            return

        for series in self._series_lookup:
            contains, info = series["line"].contains(event)
            if not contains:
                continue
            idx = info.get("ind", [None])[0]
            if idx is None:
                continue

            x = series["xs"][idx]
            y = series["ys"][idx]
            self._hover_annotation.xy = (x, y)
            self._position_hover_annotation(idx, len(series["xs"]), x, y)
            self._hover_annotation.set_text(f"{series['label']}\nn = {int(x)}\nRuntime = {y:.2f} μs")
            self._hover_annotation.set_visible(True)
            self.canvas.draw_idle()
            return

        self._hide_hover_annotation()

    def _on_pick(self, event):
        actual_line = self._legend_artist_map.get(event.artist)
        if actual_line is None:
            return
        actual_line.set_visible(not actual_line.get_visible())
        legend_line, legend_text = self._legend_entry_map.get(actual_line, (None, None))
        alpha = 1.0 if actual_line.get_visible() else 0.25
        if legend_line is not None:
            legend_line.set_alpha(alpha)
        if legend_text is not None:
            legend_text.set_alpha(alpha)
        self.canvas.draw_idle()

    def _reset_legend_state(self):
        self._legend_artist_map = {}
        self._legend_entry_map = {}

    def _draw_empty_plot(self, message: str):
        theme = self._theme or {"text": "#0f172a"}
        self._series_lookup = []
        self._reset_legend_state()
        self.ax.clear()
        self._apply_axis_style()
        self.ax.text(
            0.5,
            0.5,
            message,
            transform=self.ax.transAxes,
            ha="center",
            va="center",
            color=theme["text"],
        )
        self._build_hover_annotation()
        self.canvas.draw_idle()

    def _csv_path(self):
        outdir = self.outdir_var.get().strip()
        return os.path.join(outdir, "results.csv")

    def _update_metric_cards(self, selected_count=0, sample_count=0, best_runtime="--", best_note="Chưa có dữ liệu hợp lệ."):
        self.metric_selected.set(str(selected_count))
        self.metric_samples.set(str(sample_count))
        self.metric_best.set(best_runtime)
        self.metric_best_note.set(best_note)
        self.metric_scale.set("Log" if self.var_log_scale.get() else "Linear")
        self.metric_scale_note.set("Trục Y logarit." if self.var_log_scale.get() else "Trục Y tuyến tính.")

    def clear_plot(self):
        self.lbl.config(text="Biểu đồ đã được xóa khỏi màn hình. Lịch sử trên đĩa vẫn giữ nguyên.")
        self._update_metric_cards(
            selected_count=len(self._selected_algorithms()),
            sample_count=0,
            best_runtime="--",
            best_note="Biểu đồ đang trống.",
        )
        self._draw_empty_plot("Biểu đồ đang trống.")

    def export_png(self):
        default_dir = self.outdir_var.get().strip() or os.getcwd()
        default_name = os.path.join(default_dir, "benchmark_plot.png")
        path = filedialog.asksaveasfilename(
            title="Xuất biểu đồ ra PNG",
            initialdir=default_dir,
            initialfile=os.path.basename(default_name),
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
        )
        if not path:
            return
        try:
            self.fig.savefig(path, dpi=160, bbox_inches="tight")
            self.lbl.config(text=f"Đã xuất biểu đồ: {path}")
        except Exception as exc:
            messagebox.showerror("Lỗi xuất PNG", str(exc))

    def delete_history(self):
        csv_path = self._csv_path()
        if not os.path.exists(csv_path):
            messagebox.showinfo("Thông báo", "Không có results.csv để xóa.")
            self.refresh()
            return

        ok = messagebox.askyesno(
            "Xác nhận xóa lịch sử",
            (
                "Bạn có chắc muốn xóa toàn bộ lịch sử benchmark?\n\n"
                f"File sẽ bị xóa:\n{csv_path}\n\n"
                "Các file JSON mảng, nếu có, sẽ không bị đụng tới."
            ),
        )
        if not ok:
            return

        try:
            os.remove(csv_path)
            messagebox.showinfo("Đã xóa", "Đã xóa results.csv. Bạn có thể benchmark lại từ đầu.")
        except Exception as exc:
            messagebox.showerror("Lỗi", f"Không xóa được results.csv:\n{exc}")
        finally:
            self.refresh()

    def refresh(self):
        csv_path = self._csv_path()
        history = load_history(csv_path)
        self._last_history = history
        selected_algorithms = self._selected_algorithms()

        if not selected_algorithms:
            self.lbl.config(text="Chưa chọn thuật toán nào để hiển thị trên biểu đồ.")
            self._update_metric_cards(selected_count=0, sample_count=0, best_runtime="--", best_note="Hãy chọn ít nhất một thuật toán.")
            self._draw_empty_plot("Chọn ít nhất một thuật toán để xem biểu đồ.")
            return

        if not history:
            self.lbl.config(text=f"Không tìm thấy lịch sử benchmark tại: {csv_path}")
            self.dataset_note.set("Chưa có dataset nào trong lịch sử benchmark.")
            self.cmb_dataset.configure(values=(), state="disabled")
            self.cmb_batch.configure(values=(), state="disabled")
            self.var_dataset.set("")
            self.var_batch.set("")
            self._update_metric_cards(selected_count=len(selected_algorithms), sample_count=0, best_runtime="--", best_note="Chưa có dữ liệu benchmark.")
            self._draw_empty_plot("Chưa có dữ liệu benchmark.")
            return

        dataset_groups = self._summarize_datasets(history)
        ordered_datasets = self._sync_dataset_controls(dataset_groups)
        if not ordered_datasets:
            self.lbl.config(text=f"Không tìm thấy dataset hợp lệ trong lịch sử: {csv_path}")
            self.dataset_note.set("Lịch sử hiện tại không có dataset hợp lệ để vẽ.")
            self._update_metric_cards(selected_count=len(selected_algorithms), sample_count=0, best_runtime="--", best_note="Không có dataset hợp lệ.")
            self._draw_empty_plot("Không có dataset hợp lệ để vẽ biểu đồ.")
            return

        dataset_key = self._current_dataset_key()
        if dataset_key not in dataset_groups:
            dataset_key = ordered_datasets[0]["key"]

        dataset_group = dataset_groups[dataset_key]
        dataset_records = [record for record in history if record["dataset_key"] == dataset_key]
        batch_groups = self._summarize_batches(dataset_records)
        ordered_batches = self._sync_batch_controls(batch_groups)

        viewing_batch = self.var_scope.get() == PLOT_SCOPE_BATCH
        filtered_history = dataset_records
        batch_note = ""
        if viewing_batch:
            batch_id = self._current_batch_id()
            if batch_id not in batch_groups and ordered_batches:
                batch_id = ordered_batches[0]["batch_id"]
            if batch_id in batch_groups:
                filtered_history = [record for record in dataset_records if record["batch_id"] == batch_id]
                batch_group = batch_groups[batch_id]
                batch_note = (
                    f" | Batch: {batch_group['run_kind']} @ {self._format_timestamp(batch_group['latest_ts'])}"
                    f" | {len(batch_group['ns'])} n | {batch_group['ok_count']} mẫu OK"
                )
            else:
                filtered_history = []
        else:
            self.cmb_batch.configure(state="disabled")

        self.dataset_note.set(
            (
                f"Dataset đang xem: seed={dataset_group['seed']} | tỷ lệ âm={dataset_group['neg_ratio']:.3f} | "
                f"{len(dataset_group['ns'])} kích thước n | {dataset_group['ok_count']}/{dataset_group['total_count']} mẫu OK | "
                f"{len(dataset_group['batch_ids'])} batch | mới nhất {self._format_timestamp(dataset_group['latest_ts'])}"
            )
            + batch_note
        )

        by_alg = {alg: {} for alg in OFFICIAL_ALGORITHM_LABELS}
        ok_count = 0
        skipped_bad = 0
        skipped_legacy = 0
        per_alg_sample_count = {alg: 0 for alg in OFFICIAL_ALGORITHM_LABELS}
        for record in filtered_history:
            alg = record["algorithm"] or "Unknown"
            if alg not in by_alg:
                skipped_legacy += 1
                continue
            if not record["ok"]:
                skipped_bad += 1
                continue
            by_alg[alg].setdefault(record["n"], []).append(record["runtime_us"])
            per_alg_sample_count[alg] += 1
            ok_count += 1

        self.ax.clear()
        self._apply_axis_style()
        self._series_lookup = []
        self._reset_legend_state()
        theme = self._theme or {"plot_bg": "#ffffff"}

        plotted = 0
        plotted_lines = []
        best_alg = None
        best_runtime = None
        for alg in selected_algorithms:
            grouped = by_alg[alg]
            if not grouped:
                continue
            xs = sorted(grouped)
            ys = [sum(grouped[n]) / len(grouped[n]) for n in xs]
            mean_runtime = sum(ys) / len(ys)
            if best_runtime is None or mean_runtime < best_runtime:
                best_runtime = mean_runtime
                best_alg = alg

            style = self._series_style(alg)
            line, = self.ax.plot(
                xs,
                ys,
                label=alg,
                color=style["color"],
                marker=style["marker"],
                linewidth=style["linewidth"],
                markersize=style["markersize"],
                markeredgecolor=theme["plot_bg"],
                markeredgewidth=1.1,
            )
            line.set_pickradius(10)
            self._series_lookup.append({"line": line, "label": alg, "xs": xs, "ys": ys})
            plotted_lines.append(line)
            plotted += 1

        self._build_hover_annotation()

        missing = [alg for alg in selected_algorithms if not by_alg[alg]]
        if not plotted:
            msg = f"Không có dữ liệu hợp lệ cho {len(selected_algorithms)} thuật toán đang chọn."
            if skipped_legacy:
                msg += f" Bỏ qua {skipped_legacy} bản ghi nhãn cũ."
            self.lbl.config(text=f"{msg} Nguồn: {csv_path}")
            self._update_metric_cards(
                selected_count=len(selected_algorithms),
                sample_count=0,
                best_runtime="--",
                best_note="Không có mẫu hợp lệ để tính toán.",
            )
            self._draw_empty_plot("Không có mẫu hợp lệ để vẽ biểu đồ.")
            return

        legend = self.ax.legend(title="Thuật toán")
        if legend:
            theme = self._theme or {"panel": "#ffffff", "grid": "#e2e8f0", "text": "#0f172a"}
            legend.get_frame().set_facecolor(theme["panel"])
            legend.get_frame().set_edgecolor(theme["grid"])
            legend.get_title().set_color(theme["text"])
            for text in legend.get_texts():
                text.set_color(theme["text"])

            for legend_line, actual_line, legend_text in zip(legend.get_lines(), plotted_lines, legend.get_texts()):
                legend_line.set_picker(5)
                legend_text.set_picker(True)
                self._legend_artist_map[legend_line] = actual_line
                self._legend_artist_map[legend_text] = actual_line
                self._legend_entry_map[actual_line] = (legend_line, legend_text)

        scope_text = "dataset" if not viewing_batch else "1 batch"
        status = (
            f"Đang xem {plotted}/{len(selected_algorithms)} thuật toán đã chọn | "
            f"{ok_count} mẫu hợp lệ | seed={dataset_group['seed']} | ratio={dataset_group['neg_ratio']:.3f} | scope={scope_text}"
        )
        if missing:
            status += f" | Thiếu: {', '.join(missing)}"
        if skipped_bad:
            status += f" | Bỏ qua {skipped_bad} mẫu lỗi"
        if skipped_legacy:
            status += f" | Bỏ qua {skipped_legacy} bản ghi nhãn cũ"
        status += f" | Nguồn: {csv_path}"
        self.lbl.config(text=status)

        best_runtime_text = f"{best_runtime:.2f} μs" if best_runtime is not None else "--"
        best_note = best_alg if best_alg else "Chưa có dữ liệu hợp lệ."
        self._update_metric_cards(
            selected_count=plotted,
            sample_count=sum(per_alg_sample_count[alg] for alg in selected_algorithms),
            best_runtime=best_runtime_text,
            best_note=best_note,
        )
        self.canvas.draw_idle()
