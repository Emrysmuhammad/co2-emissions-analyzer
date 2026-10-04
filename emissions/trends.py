import numpy as np
import pandas as pd

from emissions.config import SOURCE_COLUMNS


def country_series(frame, country, column="co2", start_year=None):
    series = frame[frame["country"] == country].set_index("year")[column].dropna()
    if start_year is not None:
        series = series[series.index >= start_year]
    return series


def _values_in_year(frame, year, column):
    return frame[frame["year"] == year].set_index("country")[column]


def change_between(countries, start_year, end_year, column="co2", min_start_value=10.0):
    table = pd.DataFrame(
        {
            "start": _values_in_year(countries, start_year, column),
            "end": _values_in_year(countries, end_year, column),
        }
    ).dropna()
    table.index.name = "country"
    table = table[table["start"] >= min_start_value].copy()
    table["change"] = table["end"] - table["start"]
    table["change_pct"] = table["change"] / table["start"] * 100
    return table.reset_index()


def biggest_reducers(countries, start_year, end_year, n=10, min_start_value=10.0):
    table = change_between(countries, start_year, end_year, "co2", min_start_value)
    return table.nsmallest(n, "change").reset_index(drop=True)


def biggest_growers(countries, start_year, end_year, n=10, min_start_value=10.0):
    table = change_between(countries, start_year, end_year, "co2", min_start_value)
    return table.nlargest(n, "change").reset_index(drop=True)


def peaked_countries(countries, latest, min_peak_value=20.0, min_years_since_peak=10, min_drop_pct=10.0):
    valid = countries.dropna(subset=["co2"])
    peaks = valid.loc[valid.groupby("country")["co2"].idxmax(), ["country", "year", "co2"]]
    peaks = peaks.rename(columns={"year": "peak_year", "co2": "peak_co2"})

    current = _values_in_year(valid, latest, "co2")
    peaks["current_co2"] = peaks["country"].map(current)
    peaks = peaks.dropna(subset=["current_co2"])
    peaks["drop_pct"] = (peaks["peak_co2"] - peaks["current_co2"]) / peaks["peak_co2"] * 100

    keep = (
        (peaks["peak_co2"] >= min_peak_value)
        & (latest - peaks["peak_year"] >= min_years_since_peak)
        & (peaks["drop_pct"] >= min_drop_pct)
    )
    return peaks[keep].sort_values("peak_co2", ascending=False).reset_index(drop=True)


def decoupled_countries(countries, start_year, end_year, min_population=1_000_000, min_start_co2=10.0):
    table = pd.DataFrame(
        {
            "co2_start": _values_in_year(countries, start_year, "co2"),
            "co2_end": _values_in_year(countries, end_year, "co2"),
            "gdp_start": _values_in_year(countries, start_year, "gdp"),
            "gdp_end": _values_in_year(countries, end_year, "gdp"),
            "population": _values_in_year(countries, end_year, "population"),
        }
    ).dropna()
    table.index.name = "country"
    table = table[(table["population"] >= min_population) & (table["co2_start"] >= min_start_co2)].copy()

    table["gdp_change_pct"] = (table["gdp_end"] / table["gdp_start"] - 1) * 100
    table["co2_change_pct"] = (table["co2_end"] / table["co2_start"] - 1) * 100

    decoupled = table[(table["gdp_change_pct"] > 0) & (table["co2_change_pct"] < 0)]
    return decoupled.sort_values("co2_change_pct").reset_index()


def source_mix(frame, name):
    rows = frame[frame["country"] == name].set_index("year")[SOURCE_COLUMNS]
    return rows.dropna(how="all").fillna(0)


def income_emissions_table(countries, year):
    rows = countries[countries["year"] == year].copy()
    rows["gdp_per_capita"] = rows["gdp"] / rows["population"]
    rows = rows.dropna(subset=["gdp_per_capita", "co2_per_capita", "population"])
    rows = rows[(rows["gdp_per_capita"] > 0) & (rows["co2_per_capita"] > 0)]
    return rows.reset_index(drop=True)


def income_emissions_correlation(table):
    income = np.log10(table["gdp_per_capita"])
    emissions = np.log10(table["co2_per_capita"])
    return float(np.corrcoef(income, emissions)[0, 1])


def world_summary(dataset, year, baseline_year=1950):
    world = dataset.world["co2"].dropna()
    return {
        "year": year,
        "total": float(world.loc[year]),
        "baseline_year": baseline_year,
        "baseline": float(world.loc[baseline_year]),
        "multiple": float(world.loc[year] / world.loc[baseline_year]),
        "peak_year": int(world.idxmax()),
    }