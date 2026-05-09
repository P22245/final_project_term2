import threading
import csv
import os
import numpy as np

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_DIR, "gameplay_stats.csv")

# Color palette (same as stats_visualizer)
DARK_BG  = "#0d0d1a"
PANEL_BG = "#1a1a2e"
GRID_COL = "#2a2a45"
TEXT_COL = "#e0e0f0"
GREEN = "#3ddc84"
RED = "#e05252"
YELLOW = "#f9a825"
BLUE = "#4fc3f7"
PURPLE = "#ab47bc"
TABS = ["Histogram", "Boxplot", "Scatter", "Table"]


def _load_data():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _parse(rows):
    kills, body_hp, spreads, waves, results = [], [], [], [], []
    for r in rows:
        try:
            kills.append(int(r["bacteria_killed"]))
            body_hp.append(float(r["final_body_hp"]))
            spreads.append(int(r["infection_spread_count"]))
            waves.append(int(r["waves_survived"]))
            results.append(r["result"].strip().lower())
        except (ValueError, KeyError):
            continue
    return (np.array(kills), np.array(body_hp),
            np.array(spreads), np.array(waves), results)


def _style_ax(ax, title, xlabel="", ylabel=""):
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRID_COL)
    ax.set_title(title, color=TEXT_COL, fontsize=12, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT_COL, fontsize=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT_COL, fontsize=9)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)


# Plot functions (one per tab)

def _plot_histogram(fig, kills, n):
    fig.clear()
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(DARK_BG)
    if n == 0:
        ax.set_facecolor(PANEL_BG)
        ax.text(0.5, 0.5, "No data yet", transform=ax.transAxes,ha="center", va="center", color=TEXT_COL, fontsize=14)
        return
    n_bins = max(8, n // 6)
    counts, _, patches = ax.hist(kills, bins=n_bins, color=GREEN,edgecolor=DARK_BG, linewidth=0.6)
    max_c = max(counts) if max(counts) > 0 else 1
    for patch, c in zip(patches, counts):
        patch.set_facecolor(plt.cm.YlGn(0.35 + 0.65 * c / max_c))
    ax.axvline(np.mean(kills),color=YELLOW, linestyle="--",linewidth=1.8,label=f"Mean: {np.mean(kills):.1f}")
    ax.axvline(np.median(kills), color=BLUE,linestyle=":",linewidth=1.8, label=f"Median: {np.median(kills):.1f}")
    from matplotlib.patches import Patch
    legend_elements = [plt.Line2D([0],[0], color=YELLOW,linestyle="--", linewidth=1.8, label=f"Mean: {np.mean(kills):.1f}"),
        plt.Line2D([0],[0], color=BLUE,linestyle=":",  linewidth=1.8, label=f"Median: {np.median(kills):.1f}"),
        Patch(facecolor=plt.cm.YlGn(1.0),label="High frequency (many sessions)"),
        Patch(facecolor=plt.cm.YlGn(0.35),label="Low frequency (few sessions)")]
    ax.legend(handles=legend_elements, fontsize=9,facecolor=PANEL_BG, labelcolor=TEXT_COL, edgecolor=GRID_COL)
    _style_ax(ax, f"Bacteria Killed — Distribution  (n={n})","Kill Count", "Sessions")


def _plot_boxplot(fig, body_hp, results, n):
    fig.clear()
    fig.patch.set_facecolor(DARK_BG)
    if n == 0:
        ax = fig.add_subplot(111)
        ax.set_facecolor(PANEL_BG)
        ax.text(0.5, 0.5, "No data yet", transform=ax.transAxes,
                ha="center", va="center", color=TEXT_COL, fontsize=14)
        return

    # boxplot
    ax = fig.add_axes([0.08, 0.08, 0.89, 0.86])

    group_order = ["win", "loss", "quit"]
    group_colors = {"win": GREEN, "loss": RED, "quit": YELLOW}
    box_data, box_labels, box_colors = [], [], []
    for res in group_order:
        idx = [i for i, r in enumerate(results) if r == res]
        if idx:
            box_data.append(body_hp[idx])
            box_labels.append(res.upper())
            box_colors.append(group_colors[res])

    if box_data:
        bp = ax.boxplot(box_data, patch_artist=True, labels=box_labels,widths=0.45,medianprops=dict(color="white", linewidth=2.5),
                        whiskerprops=dict(color=TEXT_COL, linewidth=1.5),capprops=dict(color=TEXT_COL, linewidth=2.0),
                        flierprops=dict(marker="o", markerfacecolor=TEXT_COL,markeredgecolor="none", markersize=5))
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.80)

    ax.set_title(f"Final Body HP — by Result  (n={n})",color=TEXT_COL, fontsize=12, fontweight="bold",pad=8, loc="left")
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRID_COL)
    ax.set_xlabel("Result", color=TEXT_COL, fontsize=9)
    ax.set_ylabel("Body HP", color=TEXT_COL, fontsize=9)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)

    col_labels = [""] + box_labels
    stat_rows  = [["Mean"]+[f"{np.mean(d):.0f}"for d in box_data],["Median"] + [f"{np.median(d):.0f}" for d in box_data],
        ["Min"]+ [f"{int(np.min(d))}"for d in box_data],["Max"]+ [f"{int(np.max(d))}"for d in box_data],
        ["SD"]+ [f"{np.std(d):.0f}"for d in box_data],["n"]+ [f"{len(d)}" for d in box_data]]

    ax_tbl = fig.add_axes([0.63, 0.78, 0.29, 0.20])
    ax_tbl.axis("off")
    ax_tbl.set_facecolor(DARK_BG)

    tbl = ax_tbl.table(cellText=stat_rows, colLabels=col_labels,loc="center", cellLoc="center",bbox=[0, 0, 1, 1])
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)

    for j in range(len(col_labels)):
        cell = tbl[0, j]
        cell.set_facecolor("#1e3a5f")
        cell.set_text_props(color=box_colors[j-1] if j > 0 else BLUE,fontweight="bold")
        cell.set_edgecolor(GRID_COL)

    for i in range(len(stat_rows)):
        for j in range(len(col_labels)):
            cell = tbl[i+1, j]
            cell.set_facecolor(PANEL_BG if i % 2 == 0 else "#1f1f38")
            cell.set_edgecolor(GRID_COL)
            if j == 0:
                cell.set_text_props(color=TEXT_COL, fontweight="bold")
            else:
                cell.set_text_props(color=box_colors[j-1])


def _plot_scatter(fig, spreads, body_hp, results, n):
    fig.clear()
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(DARK_BG)
    if n == 0:
        ax.set_facecolor(PANEL_BG)
        ax.text(0.5, 0.5, "No data yet", transform=ax.transAxes,ha="center", va="center", color=TEXT_COL, fontsize=14)
        return
    color_map = {"win": GREEN, "loss": RED, "quit": YELLOW}
    plotted = set()
    for i, res in enumerate(results):
        color = color_map.get(res, BLUE)
        label = res.upper() if res not in plotted else None
        ax.scatter(spreads[i], body_hp[i], c=color, s=60, alpha=0.75,edgecolors="white", linewidths=0.3, label=label)
        plotted.add(res)
    if len(spreads) >= 3:
        z  = np.polyfit(spreads, body_hp, 1)
        p  = np.poly1d(z)
        xs = np.linspace(spreads.min(), spreads.max(), 100)
        ax.plot(xs, p(xs), color=PURPLE, linewidth=1.8, linestyle="--",alpha=0.85, label="Trend")
    ax.legend(fontsize=9, facecolor=PANEL_BG, labelcolor=TEXT_COL, edgecolor=GRID_COL)
    _style_ax(ax, f"Infection Spreads vs Final Body HP  (n={n})","Infection Spread Count", "Final Body HP")


def _plot_table(fig, kills, body_hp, waves, spreads, results, n):
    fig.clear()
    ax = fig.add_subplot(111)
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    ax.axis("off")
    ax.set_title("Statistical Summary", color=TEXT_COL, fontsize=13,fontweight="bold", pad=14)
    if n == 0:
        ax.text(0.5, 0.5, "No data yet", transform=ax.transAxes,ha="center", va="center", color=TEXT_COL, fontsize=14)
        return
    numeric = {"bacteria_killed":kills,"final_body_hp":body_hp,"waves_survived":waves,"infection_spread_count":spreads,}
    col_headers = ["Feature", "Mean", "Median", "Min", "Max", "SD"]
    table_rows = []
    for name, arr in numeric.items():
        table_rows.append([name,
            f"{np.mean(arr):.1f}", f"{np.median(arr):.1f}",
            f"{int(np.min(arr))}", f"{int(np.max(arr))}", f"{np.std(arr):.1f}"])
    win_n = results.count("win")
    loss_n = results.count("loss")
    quit_n = results.count("quit")
    mode = max(["win","loss","quit"], key=lambda x: results.count(x))
    table_rows.append(["result",f"win={win_n}", f"loss={loss_n}", f"quit={quit_n}", f"n={n}", f"mode={mode}"])

    tbl = ax.table(cellText=table_rows, colLabels=col_headers,loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 2.0)

    feat_colors = {"bacteria_killed": GREEN, "final_body_hp": BLUE,"waves_survived": YELLOW, "infection_spread_count": RED, "result": PURPLE,}
    for j in range(len(col_headers)):
        cell = tbl[0, j]
        cell.set_facecolor("#1e3a5f")
        cell.set_text_props(color=BLUE, fontweight="bold")
        cell.set_edgecolor(GRID_COL)
    row_bg = [PANEL_BG, "#1f1f38"]
    for i, row in enumerate(table_rows):
        fcol = feat_colors.get(row[0], TEXT_COL)
        for j in range(len(col_headers)):
            cell = tbl[i + 1, j]
            cell.set_facecolor(row_bg[i % 2])
            cell.set_edgecolor(GRID_COL)
            if j == 0:
                cell.set_text_props(color=fcol, fontweight="bold")
            else:
                cell.set_text_props(color=TEXT_COL)


# Main window class
class StatsWindow:
    def __init__(self):
        self._root = None
        self._thread = None
        self._lock = threading.Lock()
        self._alive = False
        self._figs = {}   # tab_name -> Figure
        self._canvases  = {}   # tab_name -> FigureCanvasTkAgg

    # Public API
    def open(self):
        with self._lock:
            if self._alive and self._root:
                # bring to front
                try:
                    self._root.after(0, self._root.lift)
                except Exception:
                    pass
                return
            self._alive = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def refresh(self):
        with self._lock:
            if not self._alive or self._root is None:
                return
        try:
            self._root.after(0, self._redraw_current)
        except Exception:
            pass

    def is_open(self):
        with self._lock:
            return self._alive

    def close(self):
        with self._lock:
            self._alive = False
        try:
            if self._root:
                self._root.after(0, self._root.destroy)
        except Exception:
            pass

    # Internal
    def _run(self):
        root = tk.Tk()
        root.title("Cell Wars — Stats")
        root.configure(bg=DARK_BG)
        root.geometry("860x580")
        root.resizable(True, True)
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        with self._lock:
            self._root = root

        # style ttk notebook
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook",background=DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab",background="#1a1a2e",foreground=TEXT_COL,padding=[14, 6], font=("Consolas", 10, "bold"))
        style.map("TNotebook.Tab",background=[("selected", "#2a2a55")],foreground=[("selected", "#ffffff")])

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=6, pady=6)
        notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self._figs = {}
        self._canvases = {}
        self._notebook = notebook

        for tab_name in TABS:
            frame = tk.Frame(notebook, bg=DARK_BG)
            notebook.add(frame, text=tab_name)

            fig = plt.Figure(facecolor=DARK_BG, tight_layout=True)
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(fill="both", expand=True)

            self._figs[tab_name] = fig
            self._canvases[tab_name] = canvas

        # refresh button
        btn_frame = tk.Frame(root, bg=DARK_BG)
        btn_frame.pack(fill="x", padx=6, pady=(0, 6))
        tk.Button(btn_frame, text="↻  Refresh", command=self._redraw_current,bg="#2a2a45", fg=TEXT_COL, relief="flat",
                  font=("Consolas", 10, "bold"), padx=14, pady=4,activebackground="#3a3a65", activeforeground="white",
                  cursor="hand2").pack(side="right")
        self._status_var = tk.StringVar(value="")
        tk.Label(btn_frame, textvariable=self._status_var,bg=DARK_BG, fg="#888", font=("Consolas", 9)).pack(side="left", padx=8)

        # draw first tab
        self._redraw_tab("Histogram")
        root.mainloop()

        with self._lock:
            self._alive = False
            self._root  = None

    def _on_close(self):
        with self._lock:
            self._alive = False
        try:
            self._root.destroy()
        except Exception:
            pass

    def _on_tab_change(self, event):
        idx      = self._notebook.index("current")
        tab_name = TABS[idx]
        self._redraw_tab(tab_name)

    def _redraw_current(self):
        try:
            idx      = self._notebook.index("current")
            tab_name = TABS[idx]
        except Exception:
            tab_name = "Histogram"
        self._redraw_tab(tab_name)

    def _redraw_tab(self, tab_name):
        rows = _load_data()
        kills, body_hp, spreads, waves, results = _parse(rows)
        n = len(kills)
        fig = self._figs[tab_name]

        if tab_name == "Histogram":
            _plot_histogram(fig, kills, n)
        elif tab_name == "Boxplot":
            _plot_boxplot(fig, body_hp, results, n)
        elif tab_name == "Scatter":
            _plot_scatter(fig, spreads, body_hp, results, n)
        elif tab_name == "Table":
            _plot_table(fig, kills, body_hp, waves, spreads, results, n)

        self._canvases[tab_name].draw()
        self._status_var.set(f"Sessions loaded: {n}   |   CSV: {os.path.basename(CSV_PATH)}")


# Module-level singleton
_window: StatsWindow | None = None


def open_stats_window():
    global _window
    if _window is None:
        _window = StatsWindow()
    _window.open()


def refresh_stats():
    global _window
    if _window and _window.is_open():
        _window.refresh()