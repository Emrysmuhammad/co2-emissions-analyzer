import pandas as pd


def fmt(pattern):
    def formatter(value):
        return "n/a" if pd.isna(value) else pattern.format(value)

    return formatter


def millions(value):
    return "n/a" if pd.isna(value) else f"{value / 1_000_000:,.1f}"


def gigatonnes(value):
    return "n/a" if pd.isna(value) else f"{value / 1000:,.0f}"


text = str
year = fmt("{:.0f}")
whole = fmt("{:,.0f}")
signed_whole = fmt("{:+,.0f}")
one_decimal = fmt("{:,.1f}")
percent = fmt("{:.1f}%")
signed_percent = fmt("{:+.0f}%")

TOP_EMITTERS = [
    ("country", "Country", text),
    ("co2", "Emissions (Mt)", whole),
    ("share_global_co2", "Share of world", percent),
    ("co2_per_capita", "Tonnes per person", one_decimal),
]

PER_CAPITA = [
    ("country", "Country", text),
    ("co2_per_capita", "Tonnes per person", one_decimal),
    ("co2", "Total (Mt)", whole),
    ("population", "Population (M)", millions),
]

CUMULATIVE = [
    ("country", "Country", text),
    ("cumulative_co2", "Since 1750 (Gt)", gigatonnes),
    ("share", "Share of total", percent),
]

PEAKED = [
    ("country", "Country", text),
    ("peak_year", "Peak year", year),
    ("peak_co2", "Peak (Mt)", whole),
    ("current_co2", "Now (Mt)", whole),
    ("drop_pct", "Below peak", percent),
]

DECOUPLED = [
    ("country", "Country", text),
    ("gdp_change_pct", "GDP change", signed_percent),
    ("co2_change_pct", "CO2 change", signed_percent),
]


def change_specs(start_year, end_year):
    return [
        ("country", "Country", text),
        ("start", f"{start_year} (Mt)", whole),
        ("end", f"{end_year} (Mt)", whole),
        ("change", "Change (Mt)", signed_whole),
        ("change_pct", "Change", signed_percent),
    ]


def render_rows(table, specs):
    return [
        [formatter(record[column]) for column, _, formatter in specs]
        for record in table.to_dict("records")
    ]


def text_table(table, specs):
    headers = [title for _, title, _ in specs]
    rows = render_rows(table, specs)
    widths = [
        max([len(headers[index])] + [len(row[index]) for row in rows])
        for index in range(len(headers))
    ]

    def line(cells):
        return "  ".join(
            cell.ljust(width) if index == 0 else cell.rjust(width)
            for index, (cell, width) in enumerate(zip(cells, widths))
        )

    separator = "  ".join("-" * width for width in widths)
    return "\n".join([line(headers), separator, *(line(row) for row in rows)])