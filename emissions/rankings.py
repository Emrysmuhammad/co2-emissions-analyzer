def _year_rows(countries, year, column):
    rows = countries[countries["year"] == year]
    return rows.dropna(subset=[column])


def top_emitters(countries, year, n=10):
    rows = _year_rows(countries, year, "co2")
    columns = ["country", "co2", "share_global_co2", "co2_per_capita"]
    return rows.nlargest(n, "co2")[columns].reset_index(drop=True)


def per_capita_leaders(countries, year, n=10, min_population=1_000_000):
    rows = _year_rows(countries, year, "co2_per_capita")
    rows = rows[rows["population"] >= min_population]
    columns = ["country", "co2_per_capita", "co2", "population"]
    return rows.nlargest(n, "co2_per_capita")[columns].reset_index(drop=True)


def cumulative_emitters(countries, year, n=10):
    rows = _year_rows(countries, year, "cumulative_co2")
    total = rows["cumulative_co2"].sum()
    top = rows.nlargest(n, "cumulative_co2")[["country", "cumulative_co2"]].copy()
    top["share"] = top["cumulative_co2"] / total * 100
    return top.reset_index(drop=True)


def country_rank(countries, country, year, column="co2"):
    rows = _year_rows(countries, year, column)
    ranks = rows[column].rank(ascending=False, method="min")
    match = ranks[rows["country"] == country]
    if match.empty:
        return None
    return int(match.iloc[0]), len(rows)


def top_share(countries, year, top_n=5):
    rows = _year_rows(countries, year, "co2")
    return rows.nlargest(top_n, "co2")["co2"].sum() / rows["co2"].sum() * 100