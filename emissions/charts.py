from itertools import cycle

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from emissions.config import METRICS
from emissions.trends import country_series

PALETTE = ["#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2", "#db2777", "#4b5563"]


def math_text(text):
    return text.replace("CO2", "CO$_2$")


def style_axes(ax, grid_axis="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)


def save_figure(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def plot_trends(frame, names, path, column="co2", start_year=1950):
    title, unit = METRICS[column]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    last_year = start_year

    for color, name in zip(cycle(PALETTE), names):
        series = country_series(frame, name, column, start_year)
        if series.empty:
            continue
        last_year = max(last_year, int(series.index.max()))
        ax.plot(series.index, series.values, label=name, color=color, linewidth=2.2)

    ax.set_title(math_text(f"{title}, {start_year}-{last_year}"), loc="left", fontsize=14, fontweight="bold")
    ax.set_ylabel(math_text(unit))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.legend(frameon=False, loc="upper left")
    style_axes(ax)
    return save_figure(fig, path)


def plot_top_emitters(table, year, path):
    ordered = table.sort_values("co2")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(ordered["country"], ordered["co2"], color=PALETTE[0])

    labels = [
        f"{co2:,.0f} Mt ({share:.1f}%)"
        for co2, share in zip(ordered["co2"], ordered["share_global_co2"])
    ]
    ax.bar_label(bars, labels=labels, padding=6, fontsize=9)
    ax.margins(x=0.22)

    ax.set_title(math_text(f"Largest CO2 emitters, {year}"), loc="left", fontsize=14, fontweight="bold")
    ax.set_xlabel(math_text("Million tonnes of CO2 (share of world total)"))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    style_axes(ax, grid_axis="x")
    return save_figure(fig, path)