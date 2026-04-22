import os
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(_DIR, "gameplay_stats.csv")
CHART_PATH = os.path.join(_DIR, "stats_chart.png")

DARK_BG = "#0d0d1a"
PANEL_BG = "#1a1a2e"
GRID_COL = "#2a2a45"
TEXT_COL = "#e0e0f0"
GREEN = "#3ddc84"
RED = "#e05252"
YELLOW = "#f9a825"
BLUE = "#4fc3f7"
PURPLE = "#ab47bc"


def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"[Stats] notfound : {CSV_PATH}")
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"[Stats] load {len(rows)} sessions")
    return rows


def plot_save(rows):
    _do_plot(rows, show=False)


def plot(rows):
    _do_plot(rows, show=True)


def _style_ax(ax, title, xlabel="", ylabel=""):
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT_COL, labelsize=9)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRID_COL)
    ax.set_title(title, color=TEXT_COL, fontsize=11, fontweight="bold", pad=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=TEXT_COL, fontsize=9, labelpad=5)
    if ylabel:
        ax.set_ylabel(ylabel, color=TEXT_COL, fontsize=9, labelpad=5)
    ax.grid(axis="y", color=GRID_COL, linewidth=0.5, alpha=0.6)


def _do_plot(rows, show=True):
    if not rows:
        print("[Stats] no data")
        return

    # Parse
    kills = []
    body_hp = []
    spreads = []
    waves = []
    results = []

    for r in rows:
        try:
            kills.append(int(r["bacteria_killed"]))
            body_hp.append(float(r["final_body_hp"]))
            spreads.append(int(r["infection_spread_count"]))
            waves.append(int(r["waves_survived"]))
            results.append(r["result"].strip().lower())
        except (ValueError, KeyError):
            continue

    if not kills:
        print("[Stats] no data used")
        return

    kills   = np.array(kills)
    body_hp = np.array(body_hp)
    spreads = np.array(spreads)
    waves   = np.array(waves)
    n       = len(kills)

    # Figure layout: 2x2
    fig = plt.figure(figsize=(16, 11), facecolor=DARK_BG)
    fig.suptitle(f"Cell Wars — Gameplay Statistics Report  (n = {n} sessions)",fontsize=14, color=TEXT_COL, fontweight="bold", y=0.97)
    gs = gridspec.GridSpec(2, 2, figure=fig,hspace=0.45, wspace=0.32,top=0.92, bottom=0.07, left=0.07, right=0.97)

    # 1. HISTOGRAM — bacteria_killed
    ax1 = fig.add_subplot(gs[0, 0])
    n_bins = max(8, n // 6)
    counts, _, patches = ax1.hist(kills, bins=n_bins,color=GREEN, edgecolor=DARK_BG, linewidth=0.6)
    # gradient depends on frequency
    max_c = max(counts) if max(counts) > 0 else 1
    for patch, c in zip(patches, counts):
        patch.set_facecolor(plt.cm.YlGn(0.35 + 0.65 * c / max_c))

    ax1.axvline(np.mean(kills),color=YELLOW,linestyle="--",linewidth=1.8,label=f"Mean: {np.mean(kills):.1f}")
    ax1.axvline(np.median(kills), color=BLUE,linestyle=":",linewidth=1.8,label=f"Median: {np.median(kills):.1f}")
    ax1.legend(fontsize=8, facecolor=PANEL_BG, labelcolor=TEXT_COL,edgecolor=GRID_COL)
    _style_ax(ax1,"Bacteria Killed — Distribution",xlabel="Kill Count",ylabel="Number of Sessions")


    # 2. BOXPLOT — final_body_hp by result
    ax2 = fig.add_subplot(gs[0, 1])
    group_order = ["win", "loss", "quit"]
    group_colors = {"win": GREEN, "loss": RED, "quit": YELLOW}
    box_data = []
    box_labels = []
    box_colors = []

    for res in group_order:
        idx = [i for i, r in enumerate(results) if r == res]
        if idx:
            box_data.append(body_hp[idx])
            box_labels.append(res.upper())
            box_colors.append(group_colors[res])

    if box_data:
        bp = ax2.boxplot(box_data,patch_artist=True,labels=box_labels,medianprops=dict(color="white", linewidth=2.5),
            whiskerprops=dict(color=TEXT_COL, linewidth=1.2),capprops=dict(color=TEXT_COL, linewidth=1.5),flierprops=dict(marker="o", markerfacecolor=TEXT_COL,
            markeredgecolor="none", markersize=4))
        for patch, color in zip(bp["boxes"], box_colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)

        # n in each group
        for i, (label, color) in enumerate(zip(box_labels, box_colors)):
            key = label.lower()
            cnt = sum(1 for r in results if r == key)
            ax2.text(i + 1, -8,f"n={cnt}",ha="center", color=color, fontsize=8)

    ax2.set_ylim(bottom=-15, top=210)
    _style_ax(ax2,"Final Body HP — by Result",xlabel="Result",ylabel="Body HP")


    # 3. SCATTER — infection_spread_count vs final_body_hp
    ax3 = fig.add_subplot(gs[1, 0])

    result_color_map = {"win": GREEN, "loss": RED, "quit": YELLOW}
    plotted = set()
    for i, res in enumerate(results):
        color = result_color_map.get(res, BLUE)
        label = res.upper() if res not in plotted else None
        ax3.scatter(spreads[i], body_hp[i],c=color, s=50, alpha=0.75,edgecolors="white", linewidths=0.3,label=label)
        plotted.add(res)

    # trend line
    if len(spreads) >= 3:
        z  = np.polyfit(spreads, body_hp, 1)
        p  = np.poly1d(z)
        xs = np.linspace(spreads.min(),spreads.max(), 100)
        ax3.plot(xs, p(xs),color=PURPLE, linewidth=1.5,linestyle="--", alpha=0.85, label="Trend")

    ax3.legend(fontsize=8, facecolor=PANEL_BG, labelcolor=TEXT_COL,edgecolor=GRID_COL)
    _style_ax(ax3,"Infection Spreads vs Final Body HP",xlabel="Infection Spread Count",ylabel="Final Body HP")


    # 4. STATISTICAL TABLE
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.set_facecolor(PANEL_BG)
    ax4.axis("off")
    ax4.set_title("Statistical Summary", color=TEXT_COL,fontsize=11, fontweight="bold", pad=10)

    # numeric features
    numeric = {"bacteria_killed":kills,"final_body_hp":body_hp,"waves_survived":waves,"infection_spread_count":spreads}
    col_headers = ["Feature", "Mean", "Median", "Min", "Max", "SD"]
    table_rows = []

    for name, arr in numeric.items():
        table_rows.append([name,f"{np.mean(arr):.1f}",f"{np.median(arr):.1f}",f"{int(np.min(arr))}",f"{int(np.max(arr))}",f"{np.std(arr):.1f}"])

    # result frequency
    win_n  = results.count("win")
    loss_n = results.count("loss")
    quit_n = results.count("quit")
    mode   = max(["win","loss","quit"], key=lambda x: results.count(x))
    table_rows.append(["result",f"win={win_n}",f"loss={loss_n}",f"quit={quit_n}",f"n={n}",f"mode={mode}"])

    tbl = ax4.table(cellText=table_rows,colLabels=col_headers,loc="center",cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1,1.75)

    # style header row
    for j in range(len(col_headers)):
        cell = tbl[0, j]
        cell.set_facecolor("#1e3a5f")
        cell.set_text_props(color=BLUE, fontweight="bold")
        cell.set_edgecolor(GRID_COL)

    # style data rows
    feat_colors = {
        "bacteria_killed":        GREEN,
        "final_body_hp":          BLUE,
        "waves_survived":         YELLOW,
        "infection_spread_count": RED,
        "result":                 PURPLE,
    }
    row_bg = [PANEL_BG, "#1f1f38"]
    for i, row in enumerate(table_rows):
        fname = row[0]
        fcol  = feat_colors.get(fname, TEXT_COL)
        for j in range(len(col_headers)):
            cell = tbl[i + 1, j]
            cell.set_facecolor(row_bg[i % 2])
            cell.set_edgecolor(GRID_COL)
            if j == 0:
                cell.set_text_props(color=fcol, fontweight="bold")
            else:
                cell.set_text_props(color=TEXT_COL)

    # footer
    fig.text(0.5, 0.01,
             f"Data file: {os.path.basename(CSV_PATH)}   |   Total sessions: {n}",
             ha="center", color=GRID_COL, fontsize=8)

    # ── Save ──────────────────────────────────────────────
    plt.savefig(CHART_PATH, dpi=120,
                facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"[Stats] graph saved -> {CHART_PATH}")
    if show:
        plt.show()
    plt.close(fig)


if __name__ == "__main__":
    plot(load_data())
