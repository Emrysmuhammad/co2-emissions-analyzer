from emissions.config import SOURCE_LABELS
from emissions.rankings import country_rank
from emissions.trends import country_series, source_mix


def build_profile(dataset, name, baseline_gap=20):
    countries = dataset.countries
    series = country_series(countries, name, "co2")
    if series.empty:
        raise ValueError(f"No emissions data available for {name}")

    year = int(series.index.max())
    row = countries[(countries["country"] == name) & (countries["year"] == year)].iloc[0]
    baseline_year = year - baseline_gap
    baseline = series.get(baseline_year)
    change_pct = None if not baseline else (series.loc[year] / baseline - 1) * 100

    mix = source_mix(countries, name)
    sources = {}
    if year in mix.index and mix.loc[year].sum() > 0:
        shares = mix.loc[year] / mix.loc[year].sum() * 100
        sources = {SOURCE_LABELS[column]: float(share) for column, share in shares.items()}

    return {
        "name": name,
        "year": year,
        "co2": float(row["co2"]),
        "per_capita": row["co2_per_capita"],
        "share": row["share_global_co2"],
        "population": row["population"],
        "rank": country_rank(countries, name, year),
        "per_capita_rank": country_rank(countries, name, year, "co2_per_capita"),
        "peak_year": int(series.idxmax()),
        "peak": float(series.max()),
        "baseline_year": baseline_year,
        "change_pct": change_pct,
        "sources": sources,
    }