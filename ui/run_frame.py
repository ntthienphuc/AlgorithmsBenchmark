import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from algorithms import ALGORITHM_DETAILS, OFFICIAL_ALGORITHMS, OFFICIAL_ALGORITHM_LABELS
from core.generator import gen_array
from core.validation import count_signs
from history.persistence import make_batch_id, save_run
from ui.tooltips import Tooltip

ALGORITHMS = OFFICIAL_ALGORITHMS
ALGORITHMS_MAP = {name: info for name, info in ALGORITHMS}

SAVE_ARRAY_MODES = {
    "Không lưu": "never",
    "Chỉ khi lỗi": "on_error",
    "Luôn lưu": "always",
}


class RunFrame(ttk.Frame):
    def __init__(self, master, outdir_var: tk.StringVar, plot_frame):
        super().__init__(master)
        self.outdir_var = outdir_var
        self.plot_frame = plot_frame
        self._summary_rows = {}
        self._row_index = 0
        self._summary_context_key = None
        self._selected_summary_item = None
        self._tooltips = []
        self._action_buttons = []

        self.var_n = tk.StringVar(value="2000")
        self.var_seed = tk.StringVar(value="123")
        self.var_neg_ratio = tk.StringVar(value="0.5")
        self.var_runs = tk.StringVar(value="3")
        self.var_alg = tk.StringVar(value=OFFICIAL_ALGORITHM_LABELS[0])
        self.var_save_arrays = tk.StringVar(value="Chỉ khi lỗi")
        self.var_auto_refresh = tk.BooleanVar(value=True)
        self.var_status = tk.StringVar(value=f"Sẵn sàng. {len(ALGORITHMS)} chiến lược chính thức.")

        self.metric_time = tk.StringVar(value="O(?)")
        self.metric_space = tk.StringVar(value="O(?)")
        self.metric_neg = tk.StringVar(value="~ 0")
        self.metric_pos = tk.StringVar(value="~ 0")
        self.metric_note = tk.StringVar(value="Cùng một base array sẽ được dùng cho mọi benchmark.")
        self.summary_context = tk.StringVar(value="Bảng tổng kết đang theo dõi một ngữ cảnh benchmark duy nhất.")
        self.summary_stats = tk.StringVar(value="0 dòng | 0 đúng")
        self.last_result_title = tk.StringVar(value="Chưa có benchmark nào được chạy.")
        self.last_result_summary = tk.StringVar(value="Chọn tham số rồi chạy preview hoặc benchmark.")
        self.last_result_checks = tk.StringVar(value="Partition / k / tổng thể sẽ hiển thị tại đây.")
        self.last_result_output = tk.StringVar(value="CSV / JSON output sẽ hiện sau khi chạy.")
        self.demo_title = tk.StringVar(value="Demo trực quan theo dòng đang chọn")
        self.demo_caption = tk.StringVar(value="Chọn một dòng trong bảng tổng kết để xem before/after và chi tiết lần chạy đó.")
        self.demo_before_stats = tk.StringVar(value="Before: chưa có dữ liệu.")
        self.demo_after_stats = tk.StringVar(value="After: chưa có kết quả.")
        self.demo_boundary = tk.StringVar(value="Bấm preview hoặc chọn một dòng benchmark để cập nhật demo.")
        self.focus_name = tk.StringVar(value="Chưa chọn dòng")
        self.focus_status = tk.StringVar(value="Chưa có kết quả")
        self.focus_meta = tk.StringVar(value="Preview dataset hoặc chạy benchmark để bắt đầu.")
        self._demo_state = {"before": None, "after": None, "k": None}
        self._demo_theme = None
        self._demo_redraw_job = None

        self._build_ui()
        self._install_scroll_bindings()
        self._bind_live_updates()
        self._update_alg_details()
        self._refresh_dashboard()
        self._reset_visual_demo()

    def _build_ui(self):
        header = ttk.Frame(self, padding=(14, 12), style="Hero.TFrame")
        header.pack(fill="x")
        title_block = ttk.Frame(header, style="Hero.TFrame")
        title_block.pack(side="left")
        ttk.Label(title_block, text="Benchmark Studio", style="Hero.Title.TLabel").pack(anchor="w")
        ttk.Label(
            title_block,
            text=f"{len(ALGORITHMS)} chiến lược chính thức | cùng base array | runtime trung bình",
            style="Hero.Sub.TLabel",
        ).pack(anchor="w", pady=(2, 0))
        chip_bar = ttk.Frame(header, style="Hero.TFrame")
        chip_bar.pack(side="right")
        ttk.Label(chip_bar, text="Preview", style="Chip.TLabel").pack(side="left")
        ttk.Label(chip_bar, text="Fair benchmark", style="ChipAccent.TLabel").pack(side="left", padx=(8, 0))

        body_host = ttk.Frame(self)
        body_host.pack(fill="both", expand=True)
        self.body_canvas = tk.Canvas(body_host, highlightthickness=0, borderwidth=0)
        self.body_canvas.pack(side="left", fill="both", expand=True)
        self.body_scroll_y = ttk.Scrollbar(body_host, orient="vertical", command=self.body_canvas.yview)
        self.body_scroll_y.pack(side="right", fill="y")
        self.body_canvas.configure(yscrollcommand=self.body_scroll_y.set)

        self.body_content = ttk.Frame(self.body_canvas, padding=(10, 8))
        self._body_window = self.body_canvas.create_window((0, 0), window=self.body_content, anchor="nw")
        self.body_content.bind("<Configure>", self._on_body_content_configure)
        self.body_canvas.bind("<Configure>", self._on_body_canvas_configure)

        self.body_content.columnconfigure(0, weight=3)
        self.body_content.columnconfigure(1, weight=2)

        left_panel = ttk.Frame(self.body_content)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right_panel = ttk.Frame(self.body_content)
        right_panel.grid(row=0, column=1, sticky="nsew")

        inputs = ttk.LabelFrame(left_panel, text="Thiết lập benchmark", padding=(12, 10), style="Card.TLabelframe")
        inputs.pack(fill="x")
        form = ttk.Frame(inputs)
        form.pack(fill="x")
        for column in (1, 3, 5, 7):
            form.columnconfigure(column, weight=1)

        ttk.Label(form, text="Kích thước n:").grid(row=0, column=0, sticky="w")
        ttk.Entry(form, textvariable=self.var_n).grid(row=0, column=1, sticky="ew", padx=(6, 14))
        ttk.Label(form, text="Seed:").grid(row=0, column=2, sticky="w")
        ttk.Entry(form, textvariable=self.var_seed).grid(row=0, column=3, sticky="ew", padx=(6, 14))
        ttk.Label(form, text="Tỷ lệ âm (0..1):").grid(row=0, column=4, sticky="w")
        ttk.Entry(form, textvariable=self.var_neg_ratio).grid(row=0, column=5, sticky="ew", padx=(6, 14))
        ttk.Label(form, text="Số lần chạy:").grid(row=0, column=6, sticky="w")
        ttk.Entry(form, textvariable=self.var_runs).grid(row=0, column=7, sticky="ew", padx=(6, 0))

        ttk.Label(form, text="Thuật toán:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.cmb_alg = ttk.Combobox(
            form,
            textvariable=self.var_alg,
            values=OFFICIAL_ALGORITHM_LABELS,
            state="readonly",
        )
        self.cmb_alg.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(6, 14), pady=(8, 0))
        self.cmb_alg.bind("<<ComboboxSelected>>", lambda _e: self._on_alg_change())
        self._tooltips.append(Tooltip(self.cmb_alg, "Chọn một chiến lược chính để chạy benchmark."))

        ttk.Label(form, text="Lưu mảng:").grid(row=1, column=4, sticky="w", pady=(8, 0))
        self.cmb_save = ttk.Combobox(
            form,
            textvariable=self.var_save_arrays,
            values=list(SAVE_ARRAY_MODES),
            state="readonly",
        )
        self.cmb_save.grid(row=1, column=5, sticky="ew", padx=(6, 14), pady=(8, 0))
        self._tooltips.append(
            Tooltip(
                self.cmb_save,
                "Mặc định chỉ lưu file JSON khi kết quả sai để thư mục output gọn hơn.",
            )
        )

        self.chk_auto = ttk.Checkbutton(form, text="Tự làm mới biểu đồ", variable=self.var_auto_refresh)
        self.chk_auto.grid(row=1, column=6, columnspan=2, sticky="w", padx=(0, 0), pady=(8, 0))

        ttk.Label(form, text="Thư mục lưu kết quả:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(form, textvariable=self.outdir_var).grid(row=2, column=1, columnspan=6, sticky="ew", padx=(6, 8), pady=(8, 0))
        ttk.Button(form, text="Chọn thư mục...", command=self.choose_outdir).grid(row=2, column=7, sticky="ew", pady=(8, 0))

        actions = ttk.LabelFrame(left_panel, text="Thao tác", padding=(12, 10), style="Card.TLabelframe")
        actions.pack(fill="x", pady=(10, 0))
        action_grid = ttk.Frame(actions)
        action_grid.pack(fill="x")
        for column in range(4):
            action_grid.columnconfigure(column, weight=1)
        self.btn_preview = ttk.Button(action_grid, text="Xem trước dữ liệu", command=self.preview_dataset)
        self.btn_preview.grid(row=0, column=0, sticky="ew")
        self.btn_run = ttk.Button(action_grid, text="Chạy 1 thuật toán", command=self.run_once)
        self.btn_run.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.btn_run_all = ttk.Button(
            action_grid,
            text=f"Benchmark {len(ALGORITHMS)} thuật toán",
            command=self.run_all,
            style="Accent.TButton",
        )
        self.btn_run_all.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        self.btn_refresh_plot = ttk.Button(action_grid, text="Làm mới biểu đồ", command=self.plot_frame.refresh)
        self.btn_refresh_plot.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        self.btn_clear_log = ttk.Button(action_grid, text="Xóa log", command=self._clear_log)
        self.btn_clear_log.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        self.btn_clear_summary = ttk.Button(action_grid, text="Xóa bảng tổng kết", command=self._clear_summary)
        self.btn_clear_summary.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(8, 0))
        self._action_buttons.extend(
            [self.btn_preview, self.btn_run, self.btn_run_all, self.btn_refresh_plot, self.btn_clear_log, self.btn_clear_summary]
        )
        self._tooltips.append(Tooltip(self.btn_preview, "Sinh thử đúng bộ dữ liệu theo input hiện tại và ghi preview ra log."))
        self._tooltips.append(Tooltip(self.btn_run, "Chạy thuật toán đang chọn trên bộ dữ liệu hiện tại."))
        self._tooltips.append(
            Tooltip(
                self.btn_run_all,
                f"Chạy toàn bộ {len(ALGORITHMS)} chiến lược trên cùng một base array.",
            )
        )

        status_card = ttk.Frame(actions, padding=(0, 8, 0, 0), style="Section.TFrame")
        status_card.pack(fill="x", pady=(10, 0))
        ttk.Label(status_card, textvariable=self.var_status, style="Section.Sub.TLabel").pack(side="left")
        self.progress = ttk.Progressbar(status_card, mode="indeterminate", length=180)
        self.progress.pack(side="right")

        self.summary_card = ttk.LabelFrame(left_panel, text="Bảng tổng kết", padding=(12, 10), style="Card.TLabelframe")
        self.summary_card.pack(fill="both", expand=True, pady=(10, 0))
        summary_toolbar = ttk.Frame(self.summary_card)
        summary_toolbar.pack(fill="x")
        ttk.Label(summary_toolbar, text="1. Preview dataset", style="Chip.TLabel").pack(side="left")
        ttk.Label(summary_toolbar, text="2. Run / Benchmark", style="ChipAccent.TLabel").pack(side="left", padx=(8, 0))
        ttk.Label(summary_toolbar, text="3. Chọn 1 dòng để xem demo", style="SlateChip.TLabel").pack(side="left", padx=(8, 0))
        ttk.Label(summary_toolbar, textvariable=self.summary_stats, style="AccentSubtleChip.TLabel").pack(side="right")
        ttk.Label(self.summary_card, textvariable=self.summary_context, style="PanelSubtle.TLabel", wraplength=700, justify="left").pack(anchor="w", pady=(8, 0))

        summary = ttk.Frame(self.summary_card)
        summary.pack(fill="both", expand=True, pady=(6, 0))
        summary.columnconfigure(0, weight=1)
        summary.rowconfigure(0, weight=1)

        columns = ("algorithm", "runtime", "ok", "partition", "k_ok", "k", "neg", "pos", "stability", "memory")
        self.summary = ttk.Treeview(summary, columns=columns, show="headings", height=8, style="Summary.Treeview")
        self.summary.heading("algorithm", text="Thuật toán")
        self.summary.heading("runtime", text="Runtime (μs)")
        self.summary.heading("ok", text="Tổng")
        self.summary.heading("partition", text="Phân hoạch")
        self.summary.heading("k_ok", text="k đúng")
        self.summary.heading("k", text="k")
        self.summary.heading("neg", text="Âm")
        self.summary.heading("pos", text="Dương")
        self.summary.heading("stability", text="Ổn định")
        self.summary.heading("memory", text="Bộ nhớ")

        self.summary.column("algorithm", width=240, anchor="w")
        self.summary.column("runtime", width=120, anchor="center")
        self.summary.column("ok", width=60, anchor="center")
        self.summary.column("partition", width=90, anchor="center")
        self.summary.column("k_ok", width=70, anchor="center")
        self.summary.column("k", width=55, anchor="center")
        self.summary.column("neg", width=65, anchor="center")
        self.summary.column("pos", width=65, anchor="center")
        self.summary.column("stability", width=100, anchor="center")
        self.summary.column("memory", width=90, anchor="center")

        self.summary_scroll = ttk.Scrollbar(summary, orient="vertical", command=self.summary.yview)
        self.summary_scroll_x = ttk.Scrollbar(summary, orient="horizontal", command=self.summary.xview)
        self.summary.configure(yscrollcommand=self.summary_scroll.set, xscrollcommand=self.summary_scroll_x.set)
        self.summary.bind("<<TreeviewSelect>>", self._on_summary_select)
        self.summary.bind("<Double-1>", self._inspect_summary_row)

        self.summary.grid(row=0, column=0, sticky="nsew")
        self.summary_scroll.grid(row=0, column=1, sticky="ns")
        self.summary_scroll_x.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        self.demo_card = ttk.LabelFrame(left_panel, text="Demo trực quan của dòng đang chọn", padding=(12, 10), style="Card.TLabelframe")
        self.demo_card.pack(fill="both", expand=True, pady=(10, 0))
        ttk.Label(self.demo_card, textvariable=self.demo_title, style="Section.Title.TLabel").pack(anchor="w")
        ttk.Label(
            self.demo_card,
            textvariable=self.demo_caption,
            style="PanelSubtle.TLabel",
            wraplength=700,
            justify="left",
        ).pack(anchor="w", pady=(4, 8))

        focus_bar = ttk.Frame(self.demo_card)
        focus_bar.pack(fill="x", pady=(0, 8))
        ttk.Label(focus_bar, textvariable=self.focus_name, style="ChipAccent.TLabel").pack(side="left")
        self.focus_status_label = ttk.Label(focus_bar, textvariable=self.focus_status, style="WarmChip.TLabel")
        self.focus_status_label.pack(side="left", padx=(8, 0))
        ttk.Label(focus_bar, textvariable=self.summary_stats, style="Chip.TLabel").pack(side="right")
        ttk.Label(
            self.demo_card,
            textvariable=self.focus_meta,
            style="PanelSubtle.TLabel",
            wraplength=700,
            justify="left",
        ).pack(anchor="w", pady=(0, 8))

        legend_bar = ttk.Frame(self.demo_card)
        legend_bar.pack(fill="x", pady=(0, 8))
        ttk.Label(legend_bar, text="Âm", style="DangerChip.TLabel").pack(side="left")
        ttk.Label(legend_bar, text="Dương", style="SuccessChip.TLabel").pack(side="left", padx=(8, 0))
        ttk.Label(legend_bar, text="Biên k", style="WarmChip.TLabel").pack(side="left", padx=(8, 0))
        ttk.Label(legend_bar, text="Before/After cùng một base array", style="SlateChip.TLabel").pack(side="left", padx=(8, 0))

        demo_grid = ttk.Frame(self.demo_card)
        demo_grid.pack(fill="x")
        demo_grid.columnconfigure(0, weight=1)
        demo_grid.columnconfigure(1, weight=1)

        before_col = ttk.Frame(demo_grid)
        before_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        ttk.Label(before_col, text="Before", style="Info.TLabel").pack(anchor="w")
        self.canvas_before = tk.Canvas(before_col, height=84, highlightthickness=1, bd=0)
        self.canvas_before.pack(fill="x", pady=(4, 4))
        ttk.Label(before_col, textvariable=self.demo_before_stats, style="PanelSubtle.TLabel", wraplength=320, justify="left").pack(anchor="w")

        after_col = ttk.Frame(demo_grid)
        after_col.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        ttk.Label(after_col, text="After", style="Info.TLabel").pack(anchor="w")
        self.canvas_after = tk.Canvas(after_col, height=84, highlightthickness=1, bd=0)
        self.canvas_after.pack(fill="x", pady=(4, 4))
        ttk.Label(after_col, textvariable=self.demo_after_stats, style="PanelSubtle.TLabel", wraplength=320, justify="left").pack(anchor="w")

        ttk.Label(self.demo_card, textvariable=self.demo_boundary, style="Info.TLabel", wraplength=700, justify="left").pack(anchor="w", pady=(8, 8))
        demo_text_wrap = ttk.Frame(self.demo_card)
        demo_text_wrap.pack(fill="both", expand=True)
        demo_text_wrap.columnconfigure(0, weight=1)
        demo_text_wrap.rowconfigure(0, weight=1)
        self.demo_text = tk.Text(demo_text_wrap, height=7, wrap="none")
        self.demo_text_scroll_y = ttk.Scrollbar(demo_text_wrap, orient="vertical", command=self.demo_text.yview)
        self.demo_text_scroll_x = ttk.Scrollbar(demo_text_wrap, orient="horizontal", command=self.demo_text.xview)
        self.demo_text.configure(yscrollcommand=self.demo_text_scroll_y.set, xscrollcommand=self.demo_text_scroll_x.set)
        self.demo_text.grid(row=0, column=0, sticky="nsew")
        self.demo_text_scroll_y.grid(row=0, column=1, sticky="ns")
        self.demo_text_scroll_x.grid(row=1, column=0, sticky="ew")
        self.demo_text.configure(state="disabled")
        self.canvas_before.bind("<Configure>", self._schedule_demo_redraw)
        self.canvas_after.bind("<Configure>", self._schedule_demo_redraw)

        self.log_card = ttk.LabelFrame(left_panel, text="Log chạy benchmark", padding=(12, 10), style="Card.TLabelframe")
        self.log_card.pack(fill="both", expand=True, pady=(10, 0))
        ttk.Label(
            self.log_card,
            text="Chọn một dòng trong bảng tổng kết để xem demo trực quan và chi tiết của lần chạy đó. Double-click để mở popup chi tiết.",
            style="PanelSubtle.TLabel",
            wraplength=700,
            justify="left",
        ).pack(anchor="w")
        log_wrap = ttk.Frame(self.log_card)
        log_wrap.pack(fill="both", expand=True, pady=(6, 0))
        log_wrap.columnconfigure(0, weight=1)
        log_wrap.rowconfigure(0, weight=1)
        self.txt = tk.Text(log_wrap, height=10, wrap="none")
        self.txt_scroll_y = ttk.Scrollbar(log_wrap, orient="vertical", command=self.txt.yview)
        self.txt_scroll_x = ttk.Scrollbar(log_wrap, orient="horizontal", command=self.txt.xview)
        self.txt.configure(yscrollcommand=self.txt_scroll_y.set, xscrollcommand=self.txt_scroll_x.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        self.txt_scroll_y.grid(row=0, column=1, sticky="ns")
        self.txt_scroll_x.grid(row=1, column=0, sticky="ew")
        self.txt.configure(state="disabled")

        metrics = ttk.Frame(right_panel)
        metrics.pack(fill="x", pady=(10, 0))
        metric_row1 = ttk.Frame(metrics)
        metric_row1.pack(fill="x")
        self._build_metric_card(metric_row1, "Metric.TFrame", "Metric.Label.TLabel", "Metric.Value.TLabel", "Metric.Help.TLabel", "Time", self.metric_time, "Độ phức tạp thời gian của chiến lược đang chọn").pack(side="left", fill="x", expand=True)
        self._build_metric_card(metric_row1, "MetricAlt.TFrame", "MetricAlt.Label.TLabel", "MetricAlt.Value.TLabel", "MetricAlt.Help.TLabel", "Extra space", self.metric_space, "Bộ nhớ phụ của chiến lược đang chọn").pack(side="left", fill="x", expand=True, padx=(8, 0))

        metric_row2 = ttk.Frame(metrics)
        metric_row2.pack(fill="x", pady=(8, 0))
        self._build_metric_card(metric_row2, "MetricWarm.TFrame", "MetricWarm.Label.TLabel", "MetricWarm.Value.TLabel", "MetricWarm.Help.TLabel", "Âm ước lượng", self.metric_neg, "Ước lượng theo n và tỷ lệ âm hiện tại").pack(side="left", fill="x", expand=True)
        self._build_metric_card(metric_row2, "MetricSuccess.TFrame", "MetricSuccess.Label.TLabel", "MetricSuccess.Value.TLabel", "MetricSuccess.Help.TLabel", "Dương ước lượng", self.metric_pos, "Ước lượng theo n và tỷ lệ âm hiện tại").pack(side="left", fill="x", expand=True, padx=(8, 0))

        info = ttk.LabelFrame(right_panel, text="Metadata học thuật", padding=(12, 10), style="Card.TLabelframe")
        info.pack(fill="x", pady=(10, 0))
        self.lbl_strategy = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_strategy.pack(anchor="w")
        self.lbl_complexity = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_complexity.pack(anchor="w", pady=(4, 0))
        self.lbl_memory = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_memory.pack(anchor="w", pady=(4, 0))
        self.lbl_in_place = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_in_place.pack(anchor="w", pady=(4, 0))
        self.lbl_stability = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_stability.pack(anchor="w", pady=(4, 0))
        self.lbl_deterministic = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_deterministic.pack(anchor="w", pady=(4, 0))
        self.lbl_function = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_function.pack(anchor="w", pady=(4, 0))
        self.lbl_idea = ttk.Label(info, text="", style="Info.TLabel")
        self.lbl_idea.pack(anchor="w", pady=(4, 0))
        ttk.Label(info, textvariable=self.metric_note, style="PanelSubtle.TLabel", wraplength=420, justify="left").pack(anchor="w", pady=(6, 0))

        result_card = ttk.LabelFrame(right_panel, text="Kết quả gần nhất", padding=(12, 10), style="Card.TLabelframe")
        result_card.pack(fill="x", pady=(10, 0))
        ttk.Label(result_card, textvariable=self.last_result_title, style="Section.Title.TLabel").pack(anchor="w")
        ttk.Label(
            result_card,
            text="Card này luôn bám theo preview gần nhất hoặc dòng đang chọn trong bảng tổng kết.",
            style="PanelSubtle.TLabel",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Label(result_card, textvariable=self.last_result_summary, style="Info.TLabel", wraplength=420, justify="left").pack(anchor="w", pady=(4, 0))
        ttk.Label(result_card, textvariable=self.last_result_checks, style="Info.TLabel", wraplength=420, justify="left").pack(anchor="w", pady=(4, 0))
        ttk.Label(result_card, textvariable=self.last_result_output, style="PanelSubtle.TLabel", wraplength=420, justify="left").pack(anchor="w", pady=(6, 0))

    @staticmethod
    def _build_metric_card(parent, frame_style, label_style, value_style, help_style, title, variable, help_text):
        card = ttk.Frame(parent, padding=(12, 10), style=frame_style)
        ttk.Label(card, text=title, style=label_style).pack(anchor="w")
        ttk.Label(card, textvariable=variable, style=value_style).pack(anchor="w", pady=(4, 0))
        ttk.Label(card, text=help_text, style=help_style, wraplength=200, justify="left").pack(anchor="w", pady=(4, 0))
        return card

    def _on_body_content_configure(self, _event=None):
        self.body_canvas.configure(scrollregion=self.body_canvas.bbox("all"))

    def _on_body_canvas_configure(self, _event=None):
        self.body_canvas.itemconfigure(self._body_window, width=self.body_canvas.winfo_width())

    def _install_scroll_bindings(self):
        local_scroll_roots = {
            self.summary,
            self.summary_scroll,
            self.summary_scroll_x,
            self.demo_text,
            self.demo_text_scroll_y,
            self.demo_text_scroll_x,
            self.txt,
            self.txt_scroll_y,
            self.txt_scroll_x,
        }
        self._bind_mousewheel_descendants(self.body_canvas, self._on_body_mousewheel, exclude=local_scroll_roots)
        self._bind_mousewheel_descendants(self.summary, self._on_summary_mousewheel, self._on_summary_shift_mousewheel)
        self._bind_mousewheel_descendants(self.demo_text, self._on_demo_text_mousewheel, self._on_demo_text_shift_mousewheel)
        self._bind_mousewheel_descendants(self.txt, self._on_log_mousewheel, self._on_log_shift_mousewheel)
        self.body_scroll_y.bind("<MouseWheel>", self._on_body_mousewheel, add="+")
        for scrollbar, handler in (
            (self.summary_scroll, self._on_summary_mousewheel),
            (self.summary_scroll_x, self._on_summary_shift_mousewheel),
            (self.demo_text_scroll_y, self._on_demo_text_mousewheel),
            (self.demo_text_scroll_x, self._on_demo_text_shift_mousewheel),
            (self.txt_scroll_y, self._on_log_mousewheel),
            (self.txt_scroll_x, self._on_log_shift_mousewheel),
        ):
            scrollbar.bind("<MouseWheel>", handler, add="+")
            scrollbar.bind("<Shift-MouseWheel>", handler, add="+")

    def _bind_mousewheel_descendants(self, widget, vertical_handler, horizontal_handler=None, exclude=None):
        exclude = exclude or set()
        if widget in exclude:
            return
        widget.bind("<MouseWheel>", vertical_handler, add="+")
        if horizontal_handler is not None:
            widget.bind("<Shift-MouseWheel>", horizontal_handler, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel_descendants(child, vertical_handler, horizontal_handler, exclude)

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

    def _on_body_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0 or not self._can_scroll(self.body_canvas, "y"):
            return "break"
        self.body_canvas.yview_scroll(steps, "units")
        return "break"

    def _on_summary_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0:
            return "break"
        self.summary.yview_scroll(steps, "units")
        return "break"

    def _on_summary_shift_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0:
            return "break"
        self.summary.xview_scroll(steps, "units")
        return "break"

    def _on_demo_text_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0:
            return "break"
        self.demo_text.yview_scroll(steps, "units")
        return "break"

    def _on_demo_text_shift_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0:
            return "break"
        self.demo_text.xview_scroll(steps, "units")
        return "break"

    def _on_log_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0:
            return "break"
        self.txt.yview_scroll(steps, "units")
        return "break"

    def _on_log_shift_mousewheel(self, event):
        steps = self._wheel_steps(event)
        if steps == 0:
            return "break"
        self.txt.xview_scroll(steps, "units")
        return "break"

    def _scroll_body_to_widget(self, widget):
        if not widget or not widget.winfo_ismapped():
            return
        self.update_idletasks()
        canvas_height = max(1, self.body_canvas.winfo_height())
        content_height = max(1, self.body_content.winfo_height())
        target_top = widget.winfo_y()
        target_bottom = target_top + widget.winfo_height()
        current_top = self.body_canvas.canvasy(0)
        current_bottom = current_top + canvas_height

        if target_top < current_top:
            self.body_canvas.yview_moveto(max(0.0, target_top / content_height))
        elif target_bottom > current_bottom:
            offset = max(0.0, (target_bottom - canvas_height) / content_height)
            self.body_canvas.yview_moveto(min(offset, 1.0))

    def _bind_live_updates(self):
        for variable in (self.var_n, self.var_neg_ratio, self.var_runs, self.var_alg, self.var_save_arrays):
            try:
                variable.trace_add("write", lambda *_: self._refresh_dashboard())
            except Exception:
                continue

    def apply_theme(self, theme):
        self._demo_theme = theme
        self.body_canvas.configure(background=theme["bg"])
        text_bg = theme["text_bg"]
        text_fg = theme["text_fg"]
        self.txt.configure(background=text_bg, foreground=text_fg, insertbackground=text_fg, font="TkFixedFont")
        self.txt.configure(
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=theme["border"],
            borderwidth=1,
            relief="solid",
        )
        self.demo_text.configure(background=text_bg, foreground=text_fg, insertbackground=text_fg, font="TkFixedFont")
        self.demo_text.configure(
            highlightthickness=1,
            highlightbackground=theme["border"],
            highlightcolor=theme["border"],
            borderwidth=1,
            relief="solid",
        )
        self.canvas_before.configure(background=theme["panel"], highlightbackground=theme["border"], highlightcolor=theme["border"])
        self.canvas_after.configure(background=theme["panel"], highlightbackground=theme["border"], highlightcolor=theme["border"])
        self.summary.tag_configure("best", background=theme["success_soft"], foreground=text_fg)
        self.summary.tag_configure("odd", background=theme.get("panel_alt", theme["panel"]), foreground=text_fg)
        self.summary.tag_configure("even", background=theme["panel"], foreground=text_fg)
        self.summary.tag_configure("error", background=theme["danger_soft"], foreground=text_fg)
        for tip in self._tooltips:
            tip.set_theme(theme)
        self._restore_summary_selection()
        self._schedule_demo_redraw()

    def _update_demo_text(self, text: str):
        self.demo_text.configure(state="normal")
        self.demo_text.delete("1.0", "end")
        self.demo_text.insert("1.0", text)
        self.demo_text.configure(state="disabled")

    @staticmethod
    def _format_number(value):
        if isinstance(value, float):
            return f"{value:.4f}".rstrip("0").rstrip(".")
        return str(value)

    @classmethod
    def _format_sequence(cls, values):
        return "[" + ", ".join(cls._format_number(value) for value in values) + "]"

    @classmethod
    def _format_compact_view(cls, values, edge=5):
        if len(values) <= edge * 2:
            return cls._format_sequence(values)
        left = ", ".join(cls._format_number(value) for value in values[:edge])
        right = ", ".join(cls._format_number(value) for value in values[-edge:])
        return f"[{left}, ..., {right}]"

    @classmethod
    def _format_boundary_window(cls, values, k, radius=4):
        left = values[max(0, k - radius):k]
        right = values[k:min(len(values), k + radius)]
        return f"{cls._format_sequence(left)} || {cls._format_sequence(right)}"

    def _update_visual_demo(self, title, caption, before, after=None, k=None, result=None):
        before_copy = list(before) if before is not None else None
        after_copy = list(after) if after is not None else None
        self._demo_state = {"before": before_copy, "after": after_copy, "k": k}

        self.demo_title.set(title)
        self.demo_caption.set(caption)

        if before_copy is not None:
            neg_before, pos_before, zero_before = count_signs(before_copy)
            self.demo_before_stats.set(
                f"n={len(before_copy)} | âm={neg_before} | dương={pos_before} | 0={zero_before}"
            )
        else:
            self.demo_before_stats.set("Before: chưa có dữ liệu.")

        if after_copy is None:
            self.demo_after_stats.set("Chưa có mảng kết quả sau khi chạy thuật toán.")
        else:
            neg_after, pos_after, zero_after = count_signs(after_copy)
            if result is None:
                self.demo_after_stats.set(
                    f"n={len(after_copy)} | âm={neg_after} | dương={pos_after} | 0={zero_after}"
                )
            else:
                self.demo_after_stats.set(
                    f"k={result.k} | âm={neg_after} | dương={pos_after} | partition_ok={result.partition_ok} | k_ok={result.k_ok} | ok={result.ok}"
                )

        if k is None:
            self.demo_boundary.set("Chưa có biên k để hiển thị.")
        elif after_copy is None:
            self.demo_boundary.set(
                f"Biên mục tiêu k={k}. Vạch vàng trên demo cho biết vị trí cần tách âm/dương sau khi chạy."
            )
        else:
            self.demo_boundary.set(
                f"Biên k={k} | vùng quanh biên sau khi chạy: {self._format_boundary_window(after_copy, k)}"
            )

        snapshot_lines = []
        if before_copy is not None:
            snapshot_lines.append("Before")
            snapshot_lines.append(f"  head : {self._format_compact_view(before_copy[:10])}")
            if k is not None:
                snapshot_lines.append(f"  near k: {self._format_boundary_window(before_copy, k)}")
            snapshot_lines.append(f"  tail : {self._format_compact_view(before_copy[-10:])}")
        if after_copy is not None:
            snapshot_lines.append("")
            snapshot_lines.append("After")
            snapshot_lines.append(f"  head : {self._format_compact_view(after_copy[:10])}")
            if k is not None:
                snapshot_lines.append(f"  near k: {self._format_boundary_window(after_copy, k)}")
            snapshot_lines.append(f"  tail : {self._format_compact_view(after_copy[-10:])}")
        if not snapshot_lines:
            snapshot_lines.append("Chưa có dữ liệu để hiển thị.")

        self._update_demo_text("\n".join(snapshot_lines))
        self._schedule_demo_redraw()

    def _draw_sign_strip(self, canvas, values, placeholder):
        theme = self._demo_theme or {
            "panel": "#ffffff",
            "text": "#182635",
            "subtle": "#6d7e8d",
            "border": "#d7cdbe",
            "danger": "#cf4d5e",
            "accent": "#0f8f84",
            "warning": "#b7791f",
            "warning_soft": "#fdf1d9",
        }
        width = max(canvas.winfo_width(), 120)
        height = max(canvas.winfo_height(), 50)
        canvas.delete("all")

        if not values:
            canvas.create_text(
                width / 2,
                height / 2,
                text=placeholder,
                fill=theme["subtle"],
                font=("TkDefaultFont", 9),
            )
            return

        n = len(values)
        pad_x = 6
        pad_y = 10
        usable_width = max(width - 2 * pad_x, 40)
        usable_height = max(height - 2 * pad_y - 10, 18)
        plot_top = pad_y + 10
        plot_bottom = plot_top + usable_height
        bins = min(n, max(24, usable_width // 3))
        neg_bins = [0] * bins
        pos_bins = [0] * bins
        zero_bins = [0] * bins

        for idx, value in enumerate(values):
            bin_idx = min(bins - 1, idx * bins // n)
            if value < 0:
                neg_bins[bin_idx] += 1
            elif value > 0:
                pos_bins[bin_idx] += 1
            else:
                zero_bins[bin_idx] += 1

        canvas.create_rectangle(
            pad_x,
            plot_top,
            pad_x + usable_width,
            plot_bottom,
            outline=theme["border"],
            width=1,
        )

        for bin_idx in range(bins):
            total = neg_bins[bin_idx] + pos_bins[bin_idx] + zero_bins[bin_idx]
            if total <= 0:
                continue

            x0 = pad_x + usable_width * bin_idx / bins
            x1 = pad_x + usable_width * (bin_idx + 1) / bins + 1
            y = plot_top

            neg_h = usable_height * neg_bins[bin_idx] / total
            zero_h = usable_height * zero_bins[bin_idx] / total
            pos_h = usable_height - neg_h - zero_h

            if neg_h > 0:
                canvas.create_rectangle(x0, y, x1, y + neg_h, fill=theme["danger"], width=0)
                y += neg_h
            if zero_h > 0:
                canvas.create_rectangle(x0, y, x1, y + zero_h, fill=theme["warning"], width=0)
                y += zero_h
            if pos_h > 0:
                canvas.create_rectangle(x0, y, x1, plot_bottom, fill=theme["accent"], width=0)

        k = self._demo_state.get("k")
        if isinstance(k, int) and n > 0:
            boundary_x = pad_x + usable_width * (k / n)
            canvas.create_rectangle(
                max(pad_x, boundary_x - 4),
                pad_y,
                min(pad_x + usable_width, boundary_x + 4),
                height - pad_y,
                fill=theme.get("warning_soft", theme["warning"]),
                outline="",
            )
            canvas.create_line(
                boundary_x,
                pad_y,
                boundary_x,
                height - pad_y,
                fill=theme.get("warning_soft", theme["warning"]),
                width=6,
            )
            canvas.create_line(
                boundary_x,
                pad_y,
                boundary_x,
                height - pad_y,
                fill=theme["warning"],
                width=3,
                dash=(5, 2),
            )
            label_x0 = min(max(pad_x, boundary_x + 6), max(pad_x, width - 62))
            label_y0 = 2
            label_x1 = min(width - 2, label_x0 + 54)
            label_y1 = 18
            canvas.create_rectangle(
                label_x0,
                label_y0,
                label_x1,
                label_y1,
                fill=theme["warning"],
                outline="",
            )
            canvas.create_text(
                (label_x0 + label_x1) / 2,
                (label_y0 + label_y1) / 2,
                text=f"k={k}",
                fill=theme.get("accent_text", "#ffffff"),
                font=("TkDefaultFont", 8),
            )

    def _schedule_demo_redraw(self, _event=None):
        if self._demo_redraw_job is not None:
            self.after_cancel(self._demo_redraw_job)
        self._demo_redraw_job = self.after(16, self._redraw_demo)

    def _redraw_demo(self):
        self._demo_redraw_job = None
        before = self._demo_state.get("before")
        after = self._demo_state.get("after")
        self._draw_sign_strip(self.canvas_before, before, "Preview dataset sẽ hiện ở đây.")
        self._draw_sign_strip(self.canvas_after, after, "Kết quả gần nhất sẽ hiện ở đây.")

    def _safe_inputs(self):
        try:
            n = int(self.var_n.get().strip())
        except Exception:
            n = None
        try:
            neg_ratio = float(self.var_neg_ratio.get().strip())
        except Exception:
            neg_ratio = None
        try:
            runs = int(self.var_runs.get().strip())
        except Exception:
            runs = None
        return n, neg_ratio, runs

    def _refresh_dashboard(self):
        alg_label = self.var_alg.get()
        detail = ALGORITHM_DETAILS.get(alg_label, {})
        self.metric_time.set(detail.get("time_complexity", "O(?)"))
        self.metric_space.set(detail.get("space_complexity", "O(?)"))

        n, neg_ratio, runs = self._safe_inputs()
        if isinstance(n, int) and n > 0 and isinstance(neg_ratio, float) and 0.0 <= neg_ratio <= 1.0:
            neg_est = round(n * neg_ratio)
            pos_est = n - neg_est
            self.metric_neg.set(f"~ {neg_est}")
            self.metric_pos.set(f"~ {pos_est}")
            self.metric_note.set(
                f"{alg_label} | runs={runs if isinstance(runs, int) and runs > 0 else '?'} | lưu mảng: {self.var_save_arrays.get()}"
            )
        else:
            self.metric_neg.set("~ ?")
            self.metric_pos.set("~ ?")
            self.metric_note.set("Điền input hợp lệ để xem ước lượng bộ dữ liệu.")

        self._update_alg_details()

    def _on_alg_change(self):
        self._refresh_dashboard()

    def _update_alg_details(self):
        alg_label = self.var_alg.get()
        detail = ALGORITHM_DETAILS.get(alg_label, {})
        self.lbl_strategy.config(text=f"Chiến lược thiết kế: {detail.get('strategy', '')}")
        self.lbl_complexity.config(text=f"Độ phức tạp thời gian: {detail.get('time_complexity', '')}")
        self.lbl_memory.config(text=f"Bộ nhớ phụ: {detail.get('space_complexity', '')}")
        self.lbl_in_place.config(text=f"In-place: {detail.get('in_place_text', '')}")
        self.lbl_stability.config(text=f"Tính ổn định: {detail.get('stable_text', '')}")
        self.lbl_deterministic.config(text=f"Deterministic: {detail.get('deterministic_text', '')}")
        self.lbl_function.config(text=f"Hàm public: {detail.get('function_name', '')}")
        self.lbl_idea.config(text=f"Mô tả ngắn: {detail.get('short_description', '')}")

    def _set_status(self, text: str):
        self.var_status.set(text)

    def _update_last_result(self, title: str, summary: str, checks: str, output: str):
        self.last_result_title.set(title)
        self.last_result_summary.set(summary)
        self.last_result_checks.set(checks)
        self.last_result_output.set(output)

    def _set_focus_state(self, name: str, status: str, meta: str, ok=None):
        self.focus_name.set(name)
        self.focus_status.set(status)
        self.focus_meta.set(meta)
        if ok is True:
            self.focus_status_label.configure(style="SuccessChip.TLabel")
        elif ok is False:
            self.focus_status_label.configure(style="DangerChip.TLabel")
        else:
            self.focus_status_label.configure(style="WarmChip.TLabel")

    def _update_summary_stats(self):
        total = len(self._summary_rows)
        ok_count = sum(1 for info in self._summary_rows.values() if info["ok"])
        self.summary_stats.set(f"{total} dòng | {ok_count} đúng")

    def _reset_visual_demo(self):
        self._set_focus_state(
            "Chưa chọn dòng",
            "Chưa có kết quả",
            "Preview dataset hoặc chạy benchmark để bắt đầu.",
            ok=None,
        )
        self._update_visual_demo(
            title="Demo trực quan theo dòng đang chọn",
            caption="Chọn một dòng trong bảng tổng kết để xem before/after và chi tiết lần chạy đó.",
            before=None,
            after=None,
            k=None,
        )

    def _update_last_result_from_result(self, result, title: str = "Lần chạy đã chọn"):
        self._update_last_result(
            title,
            (
                f"{result.algorithm} | {result.run_kind} | "
                f"runtime={result.runtime_us} μs | n={result.n} | k={result.k}"
            ),
            (
                f"seed={result.seed} | ratio={result.neg_ratio:.3f} | "
                f"partition_ok={result.partition_ok} | k_ok={result.k_ok} | ok={result.ok}"
            ),
            (
                f"Batch: {result.batch_id} | "
                f"CSV: {os.path.basename(result.csv_file)} | "
                f"JSON: {os.path.basename(result.array_file) if result.array_file else 'Không lưu'}"
            ),
        )

    def _show_summary_entry(self, item: str):
        info = self._summary_rows.get(item)
        if not info:
            return
        self._selected_summary_item = item
        result = info["result"]
        self._set_focus_state(
            result.algorithm,
            "Đúng" if result.ok else "Có lỗi",
            (
                f"Runtime {result.runtime_us} μs | n={result.n} | "
                f"seed={result.seed} | ratio={result.neg_ratio:.3f} | batch={result.run_kind}"
            ),
            ok=result.ok,
        )
        self._update_visual_demo(
            title=f"Dòng đang chọn | {result.algorithm}",
            caption="Demo và thông tin đang bám theo đúng dòng được chọn trong bảng tổng kết.",
            before=info.get("before"),
            after=info.get("after"),
            k=info.get("k"),
            result=result,
        )
        self._update_last_result_from_result(result)

    def _select_summary_item(self, item: str):
        if not item:
            return
        self._selected_summary_item = item
        self.summary.selection_set(item)
        self.summary.focus(item)
        self.summary.see(item)
        self._show_summary_entry(item)
        self._scroll_body_to_widget(self.summary_card)

    def _restore_summary_selection(self):
        item = self._selected_summary_item
        if not item or item not in self._summary_rows:
            return
        self.summary.selection_set(item)
        self.summary.focus(item)
        self.summary.see(item)
        self._show_summary_entry(item)

    def _set_busy(self, busy: bool, status_text: str = ""):
        button_state = "disabled" if busy else "normal"
        combo_state = "disabled" if busy else "readonly"
        for widget in self._action_buttons:
            widget.configure(state=button_state)
        self.cmb_alg.configure(state=combo_state)
        self.cmb_save.configure(state=combo_state)
        self.chk_auto.configure(state=button_state)
        if busy:
            self.progress.start(10)
        else:
            self.progress.stop()
        try:
            self.winfo_toplevel().configure(cursor="watch" if busy else "")
        except Exception:
            pass
        if status_text:
            self._set_status(status_text)
        self.update_idletasks()

    def _clear_log(self):
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.configure(state="disabled")
        self._set_status("Đã xóa log benchmark.")

    def _clear_summary(self):
        self._reset_summary_table()
        self._summary_context_key = None
        self.summary_context.set("Bảng tổng kết đang theo dõi một ngữ cảnh benchmark duy nhất.")
        self._update_summary_stats()
        self._reset_visual_demo()
        self._update_last_result(
            "Chưa có benchmark nào được chạy.",
            "Chọn tham số rồi chạy preview hoặc benchmark.",
            "Partition / k / tổng thể sẽ hiển thị tại đây.",
            "CSV / JSON output sẽ hiện sau khi chạy.",
        )
        self._set_status(f"Sẵn sàng. {len(ALGORITHMS)} chiến lược chính thức.")

    def _reset_summary_table(self):
        for item in self.summary.get_children():
            self.summary.delete(item)
        selection = self.summary.selection()
        if selection:
            self.summary.selection_remove(*selection)
        self._selected_summary_item = None
        self._summary_rows.clear()
        self._row_index = 0
        self._update_summary_stats()

    @staticmethod
    def _summary_key(n: int, seed: int, neg_ratio: float, runs: int):
        return (int(n), int(seed), f"{float(neg_ratio):.6f}", int(runs))

    @staticmethod
    def _summary_context_text(n: int, seed: int, neg_ratio: float, runs: int):
        return f"Ngữ cảnh bảng: n={n} | seed={seed} | tỷ lệ âm={neg_ratio:.3f} | runs={runs}"

    def _activate_summary_context(self, n: int, seed: int, neg_ratio: float, runs: int, force_new: bool = False):
        new_key = self._summary_key(n, seed, neg_ratio, runs)
        new_text = self._summary_context_text(n, seed, neg_ratio, runs)
        old_text = self.summary_context.get()
        had_rows = bool(self._summary_rows)

        if force_new or self._summary_context_key != new_key:
            self._reset_summary_table()
            self._summary_context_key = new_key
            self.summary_context.set(new_text)
            if had_rows and old_text != new_text:
                self._log("------------------------------------------------------------")
                self._log("Đã tách bảng tổng kết sang ngữ cảnh benchmark mới để tránh trộn dữ liệu.")
                self._log(f"Cũ: {old_text}")
                self._log(f"Mới: {new_text}")
        else:
            self.summary_context.set(new_text)

    def _add_summary_row(self, result, before, after, k):
        detail = ALGORITHM_DETAILS.get(result.algorithm, {})
        row_tag = "even" if self._row_index % 2 == 0 else "odd"
        tags = [row_tag]
        if not result.ok:
            tags.append("error")

        item = self.summary.insert(
            "",
            "end",
            values=(
                result.algorithm,
                str(result.runtime_us),
                "OK" if result.ok else "Fail",
                "OK" if result.partition_ok else "Sai",
                "OK" if result.k_ok else "Sai",
                str(result.k),
                str(result.neg_count),
                str(result.pos_count),
                detail.get("stable_text", ""),
                detail.get("space_complexity", ""),
            ),
            tags=tuple(tags),
        )
        self._row_index += 1
        self._summary_rows[item] = {
            "runtime": result.runtime_us,
            "ok": result.ok,
            "result": result,
            "before": list(before) if before is not None else None,
            "after": list(after) if after is not None else None,
            "k": k,
        }
        self._update_summary_stats()
        return item

    def _highlight_best(self):
        remembered = self._selected_summary_item
        valid_rows = {item: info for item, info in self._summary_rows.items() if info["ok"]}
        for item in self.summary.get_children():
            tags = [tag for tag in self.summary.item(item, "tags") if tag != "best"]
            self.summary.item(item, tags=tuple(tags))
        if not valid_rows:
            self._selected_summary_item = remembered
            return

        min_runtime = min(info["runtime"] for info in valid_rows.values())
        for item, info in valid_rows.items():
            if info["runtime"] != min_runtime:
                continue
            tags = list(self.summary.item(item, "tags"))
            if "best" not in tags:
                tags.append("best")
            self.summary.item(item, tags=tuple(tags))
        self._selected_summary_item = remembered

    def _on_summary_select(self, _event=None):
        selection = self.summary.selection()
        if not selection:
            return
        self._selected_summary_item = selection[0]
        self._show_summary_entry(selection[0])

    def _inspect_summary_row(self, _event=None):
        item = self.summary.focus()
        if not item:
            return
        info = self._summary_rows.get(item)
        if not info:
            return
        self._show_summary_entry(item)
        result = info["result"]
        messagebox.showinfo(
            "Chi tiết benchmark",
            (
                f"Thuật toán: {result.algorithm}\n"
                f"Runtime: {result.runtime_us} μs\n"
                f"k: {result.k}\n"
                f"Âm / Dương: {result.neg_count} / {result.pos_count}\n"
                f"partition_ok / k_ok / ok: {result.partition_ok} / {result.k_ok} / {result.ok}\n"
                f"Dataset: {result.dataset_key}\n"
                f"Batch: {result.batch_id} ({result.run_kind})\n"
                f"CSV: {result.csv_file}\n"
                f"JSON: {result.array_file or 'Không lưu'}"
            ),
        )

    def _save_array_mode(self):
        return SAVE_ARRAY_MODES.get(self.var_save_arrays.get(), "on_error")

    def choose_outdir(self):
        d = filedialog.askdirectory(
            initialdir=self.outdir_var.get() or os.getcwd(),
            title="Chọn thư mục lưu kết quả",
        )
        if d:
            self.outdir_var.set(d)

    def _log(self, text: str):
        self.txt.configure(state="normal")
        self.txt.insert("end", text + "\n")
        self.txt.see("end")
        self.txt.configure(state="disabled")

    def _parse_inputs(self):
        try:
            n = int(self.var_n.get().strip())
            if n <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Lỗi", "n không hợp lệ (phải là số nguyên dương).")
            return None

        try:
            seed = int(self.var_seed.get().strip())
        except Exception:
            messagebox.showerror("Lỗi", "Seed không hợp lệ (phải là số nguyên).")
            return None

        try:
            neg_ratio = float(self.var_neg_ratio.get().strip())
            if not (0.0 <= neg_ratio <= 1.0):
                raise ValueError
        except Exception:
            messagebox.showerror("Lỗi", "Tỷ lệ âm không hợp lệ (phải là số thực trong [0..1]).")
            return None

        try:
            runs = int(self.var_runs.get().strip())
            if runs <= 0:
                raise ValueError
        except Exception:
            messagebox.showerror("Lỗi", "Số lần chạy không hợp lệ (phải là số nguyên dương).")
            return None

        outdir = self.outdir_var.get().strip()
        if not outdir:
            messagebox.showerror("Lỗi", "Thư mục lưu kết quả không được để trống.")
            return None

        return n, seed, neg_ratio, runs, outdir

    def _run_algorithm(self, func, args, base_array, runs):
        total_runtime = 0
        last_array = None
        last_k = None
        for _ in range(runs):
            array_copy = list(base_array)
            t0 = time.perf_counter_ns()
            k = func(array_copy, *args) if args else func(array_copy)
            t1 = time.perf_counter_ns()
            total_runtime += int((t1 - t0) / 1000)
            last_array = array_copy
            last_k = k
        avg_runtime = int(total_runtime / runs)
        return avg_runtime, last_array, last_k

    def _refresh_plot_if_needed(self, seed=None, neg_ratio=None, batch_id=None):
        if seed is not None and neg_ratio is not None and hasattr(self.plot_frame, "focus_dataset"):
            self.plot_frame.focus_dataset(seed, neg_ratio, batch_id=batch_id, refresh=self.var_auto_refresh.get())
            return
        if self.var_auto_refresh.get():
            self.plot_frame.refresh()

    def preview_dataset(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        n, seed, neg_ratio, _runs, _outdir = parsed

        try:
            preview_array = gen_array(n, seed=seed, neg_ratio=neg_ratio)
            neg_count, pos_count, zero_count = count_signs(preview_array)
            selection = self.summary.selection()
            if selection:
                self.summary.selection_remove(*selection)
            self._selected_summary_item = None
            self._set_focus_state(
                "Preview dataset",
                "Chưa chạy",
                f"n={n} | seed={seed} | ratio={neg_ratio:.3f} | âm={neg_count} | dương={pos_count}",
                ok=None,
            )
            self._update_visual_demo(
                title="Preview dataset",
                caption="Preview này cho thấy dataset gốc trước khi chạy. Khi chọn một dòng trong bảng, demo sẽ chuyển sang lần run đó.",
                before=preview_array,
                after=None,
                k=neg_count,
            )
            self._scroll_body_to_widget(self.demo_card)
            self._log("------------------------------------------------------------")
            self._log(f"Preview dữ liệu | n={n} | seed={seed} | neg_ratio={neg_ratio:.3f}")
            self._log(f"Đếm âm / dương / 0: {neg_count} / {pos_count} / {zero_count}")
            self._log(f"A[0:8] = {preview_array[:8]}")
            self._log(f"A[-8:] = {preview_array[-8:]}")
            self._update_last_result(
                "Kết quả gần nhất",
                f"Preview dữ liệu | n={n} | seed={seed}",
                f"Âm / dương / 0: {neg_count} / {pos_count} / {zero_count}",
                "Chưa ghi file vì đây chỉ là preview.",
            )
            self._set_status(f"Đã preview dữ liệu: âm={neg_count}, dương={pos_count}.")
        except Exception as exc:
            messagebox.showerror("Lỗi preview", str(exc))

    def run_once(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        n, seed, neg_ratio, runs, outdir = parsed

        alg_label = self.var_alg.get()
        alg_info = ALGORITHMS_MAP.get(alg_label)
        if not alg_info:
            messagebox.showerror("Lỗi", "Thuật toán không hợp lệ.")
            return

        self._activate_summary_context(n, seed, neg_ratio, runs)
        self._set_busy(True, f"Đang chạy {alg_label}...")
        try:
            base_array = gen_array(n, seed=seed, neg_ratio=neg_ratio)
            func, needs_seed = alg_info
            args = (seed,) if needs_seed else ()
            batch_id = make_batch_id("single")

            avg_runtime, last_array, last_k = self._run_algorithm(func, args, base_array, runs)
            result = save_run(
                output_dir=outdir,
                algorithm=alg_label,
                n=n,
                seed=seed,
                neg_ratio=neg_ratio,
                runtime_us=avg_runtime,
                A=last_array,
                k=last_k,
                batch_id=batch_id,
                run_kind="single",
                save_array_mode=self._save_array_mode(),
            )

            self._log("------------------------------------------------------------")
            self._log(f"Timestamp          : {result.timestamp}")
            self._log(f"Thuật toán         : {result.algorithm}")
            self._log(f"n / seed           : {result.n} / {result.seed}")
            self._log(f"Tỷ lệ âm           : {result.neg_ratio:.3f}")
            self._log(f"Dataset            : {result.dataset_key}")
            self._log(f"Batch              : {result.batch_id} ({result.run_kind})")
            self._log(f"Số lần chạy        : {runs}")
            self._log(f"Runtime trung bình : {result.runtime_us} μs")
            self._log(f"k (số âm)          : {result.k}")
            self._log(f"Đếm âm/dương       : {result.neg_count} / {result.pos_count}")
            self._log(f"partition_ok / k_ok: {result.partition_ok} / {result.k_ok}")
            self._log(f"Kết quả tổng       : {result.ok}")
            self._log(f"Lưu mảng           : {result.array_file or 'Không lưu'}")
            self._log(f"Lưu log CSV        : {result.csv_file}")
            self._log(f"Xem nhanh          : A[0:5]={last_array[:5]}  ...  A[-5:]={last_array[-5:]}")

            item = self._add_summary_row(result, base_array, last_array, last_k)
            self._highlight_best()
            self._refresh_plot_if_needed(seed=seed, neg_ratio=neg_ratio, batch_id=batch_id)
            self._select_summary_item(item)

            final_status = f"Hoàn tất {alg_label}: {result.runtime_us} μs | OK={result.ok}"
            self._set_status(final_status)
            if not result.ok:
                messagebox.showwarning(
                    "Cảnh báo",
                    "Kết quả phân hoạch không đúng. Nếu đang để chế độ lưu mảng phù hợp, file JSON debug đã được tạo.",
                )
            else:
                messagebox.showinfo("Xong", f"{alg_label}\nRuntime trung bình: {result.runtime_us} μs")
        except Exception as exc:
            self._log(f"Lỗi khi chạy {alg_label}: {exc}")
            self._set_status("Có lỗi khi chạy benchmark.")
            messagebox.showerror("Lỗi chạy benchmark", str(exc))
        finally:
            self._set_busy(False, self.var_status.get())

    def run_all(self):
        parsed = self._parse_inputs()
        if not parsed:
            return
        n, seed, neg_ratio, runs, outdir = parsed

        self._activate_summary_context(n, seed, neg_ratio, runs, force_new=True)
        self._set_busy(True, "Đang chuẩn bị benchmark toàn bộ thuật toán...")
        try:
            base_array = gen_array(n, seed=seed, neg_ratio=neg_ratio)
            save_array_mode = self._save_array_mode()
            batch_id = make_batch_id("all")
            self._log("============================================================")
            self._log(f"Benchmark {len(ALGORITHMS)} thuật toán chính")
            self._log(f"n / seed / tỷ lệ âm / số lần: {n} / {seed} / {neg_ratio:.3f} / {runs}")
            self._log(f"Dataset group: seed={seed} | neg_ratio={neg_ratio:.3f}")
            self._log(f"Batch id: {batch_id}")
            self._log(f"Chế độ lưu mảng: {self.var_save_arrays.get()}")

            results = []
            summary_items = []
            total_algs = len(ALGORITHMS)
            for idx, (alg_label, (func, needs_seed)) in enumerate(ALGORITHMS, start=1):
                self._set_status(f"[{idx}/{total_algs}] Đang chạy {alg_label}...")
                self.update_idletasks()

                args = (seed,) if needs_seed else ()
                avg_runtime, last_array, last_k = self._run_algorithm(func, args, base_array, runs)
                result = save_run(
                    output_dir=outdir,
                    algorithm=alg_label,
                    n=n,
                    seed=seed,
                    neg_ratio=neg_ratio,
                    runtime_us=avg_runtime,
                    A=last_array,
                    k=last_k,
                    batch_id=batch_id,
                    run_kind="all",
                    save_array_mode=save_array_mode,
                )
                results.append(result)

                self._log(
                    f"{alg_label:32s} | {avg_runtime:>8d} μs | "
                    f"total={result.ok} | partition={result.partition_ok} | k={result.k_ok}"
                )
                item = self._add_summary_row(result, base_array, last_array, last_k)
                summary_items.append((item, result))

            self._highlight_best()
            self._refresh_plot_if_needed(seed=seed, neg_ratio=neg_ratio, batch_id=batch_id)

            ok_count = sum(1 for result in results if result.ok)
            valid_results = [result for result in results if result.ok]
            best = min(valid_results or results, key=lambda result: result.runtime_us)
            best_item, _ = min(
                summary_items,
                key=lambda pair: pair[1].runtime_us if pair[1].ok else float("inf"),
            )
            if not self._summary_rows.get(best_item, {}).get("ok"):
                best_item, _ = min(summary_items, key=lambda pair: pair[1].runtime_us)
            self._select_summary_item(best_item)
            final_status = (
                f"Hoàn tất benchmark: {ok_count}/{len(results)} kết quả đúng | "
                f"nhanh nhất: {best.algorithm} ({best.runtime_us} μs)"
            )
            self._set_status(final_status)
            self._log(final_status)

            if ok_count != len(results):
                messagebox.showwarning("Benchmark hoàn tất", final_status)
            else:
                messagebox.showinfo("Benchmark hoàn tất", final_status)
        except Exception as exc:
            self._log(f"Lỗi khi benchmark toàn bộ thuật toán: {exc}")
            self._set_status("Có lỗi khi benchmark toàn bộ thuật toán.")
            messagebox.showerror("Lỗi benchmark", str(exc))
        finally:
            self._set_busy(False, self.var_status.get())
