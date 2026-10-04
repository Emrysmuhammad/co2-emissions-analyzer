import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

from emissions.charts import PALETTE, math_text, save_figure, style_axes
from emissions.config import SOURCE_LABELS

SOURCE_COLORS = {
    "coal_co2": "#374151",
    "oil_co2": "#b45309",
    "gas_co2": "#0ea5e9",
    "cement_co2": "#9ca3af",
    "flaring_co2": "#ef4444",
}


def plot_changes(reducers, growers, start_year, end_year, path):
    combined = pd.concat([growers, reducers]).sort_values("change")
    colors = ["#059669" if change < 0 else "#dc2626" for change in combined["change"]]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(combined["country"], combined["change"], color=colors)
    labels = [
        f"{change:+,.0f} Mt ({pct:+.0f}%)"
        for change, pct in zip(combined["change"], combined["change_pct"])
    ]
    ax.bar_label(bars, labels=labels, padding=6, fontsize=9)
    ax.margins(x=0.25)
    ax.axvline(0, color="#374151", linewidth=1)

    ax.set_title(
        math_text(f"Biggest changes in CO2 emissions, {start_year}-{end_year}"),
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel(math_text("Change in million tonnes of CO2"))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:+,.0f}"))
    style_axes(ax, grid_axis="x")
    return save_figure(fig, path)


def plot_income_vs_emissions(table, year, correlation, path, label_top=8):
    fig, ax = plt.subplots(figsize=(10, 6))
    sizes = np.sqrt(table["population"]) / 50

    ax.scatter(
        table["gdp_per_capita"],
        table["co2_per_capita"],
        s=sizes,
        color=PALETTE[0],
        alpha=0.45,
        edgecolor="white",
        linewidth=0.5,
    )

    slope, intercept = np.polyfit(np.log10(table["gdp_per_capita"]), np.log10(table["co2_per_capita"]), 1)
    x_line = np.logspace(np.log10(table["gdp_per_capita"].min()), np.log10(table["gdp_per_capita"].max()), 50)
    ax.plot(x_line, 10 ** (intercept + slope * np.log10(x_line)), color=PALETTE[1], linewidth=2, linestyle="--")

    for row in table.nlargest(label_top, "co2").itertuples():
        ax.annotate(
            row.country,
            (row.gdp_per_capita, row.co2_per_capita),
            xytext=(6, 6),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(
        math_text(f"Richer countries emit more CO2 per person, {year}"),
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xlabel("GDP per person (international dollars, log scale)")
    ax.set_ylabel(math_text("Tonnes of CO2 per person (log scale)"))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:g}"))
    ax.text(
        0.02,
        0.96,
        f"Correlation (log scale): {correlation:.2f}\nBubble size = population",
        transform=ax.transAxes,
        va="top",
        fontsize=10,
        color="#374151",
    )
    style_axes(ax, grid_axis="both")
    return save_figure(fig, path)


def plot_emission_sources(mix, name, path, start_year=1900):
    mix = mix[mix.index >= start_year]
    if mix.empty:
        return None

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.stackplot(
        mix.index,
        [mix[column] for column in mix.columns],
        labels=[SOURCE_LABELS[column] for column in mix.columns],
        colors=[SOURCE_COLORS[column] for column in mix.columns],
    )

    ax.set_title(
        math_text(f"Where CO2 emissions come from in {name}, {int(mix.index.min())}-{int(mix.index.max())}"),
        loc="left",
        fontsize=14,
        fontweight="bold",
    )
    ax.set_ylabel(math_text("Million tonnes of CO2"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=False, loc="upper left")
    ax.margins(x=0)
    style_axes(ax)
    return save_figure(fig, path)