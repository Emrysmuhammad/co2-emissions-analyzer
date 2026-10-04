import pandas as pd
import pytest

from emissions.loader import Dataset, split_countries

YEARS = list(range(2000, 2021))

SOURCE_SHARES = {
    "coal_co2": 0.5,
    "oil_co2": 0.3,
    "gas_co2": 0.15,
    "cement_co2": 0.03,
    "flaring_co2": 0.02,
}


def make_rows(country, iso_code, population, co2_by_year, gdp_by_year=None, years=YEARS):
    rows = []
    cumulative = 0.0
    for year in years:
        co2 = co2_by_year(year)
        cumulative += co2
        row = {
            "country": country,
            "year": year,
            "iso_code": iso_code,
            "population": population,
            "gdp": gdp_by_year(year) if gdp_by_year else None,
            "co2": co2,
            "co2_per_capita": co2 * 1_000_000 / population,
            "cumulative_co2": cumulative,
        }
        for column, share in SOURCE_SHARES.items():
            row[column] = co2 * share
        rows.append(row)
    return rows


def alpha_co2(year):
    return 400 + 20 * (year - 2000) if year <= 2010 else 600 - 24 * (year - 2010)


@pytest.fixture
def frame():
    rows = []
    rows += make_rows("Alpha", "ALP", 100_000_000, alpha_co2, lambda y: 1e12 + 5e10 * (y - 2000))
    rows += make_rows("Beta", "BET", 50_000_000, lambda y: 100 + 10 * (y - 2000), lambda y: 2e11 + 1e10 * (y - 2000))
    rows += make_rows("Gamma", "GAM", 500_000, lambda y: 5 + 0.05 * (y - 2000), lambda y: 1e10)
    rows += make_rows("Delta", "DEL", 10_000_000, lambda y: 50 - y % 2000, lambda y: 1e11 + 4e9 * (y - 2000))
    rows += make_rows("Kosovo", None, 1_800_000, lambda y: 8, years=range(2000, 2016))

    countries = pd.DataFrame(rows)
    world = countries.groupby("year")[["co2"]].sum().reset_index()
    world["country"] = "World"
    world["iso_code"] = None
    for column in SOURCE_SHARES:
        world[column] = world["co2"] * SOURCE_SHARES[column]
    europe = world.assign(country="Europe", co2=world["co2"] / 4)

    combined = pd.concat([countries, world, europe], ignore_index=True)
    combined["share_global_co2"] = combined["co2"] / combined["year"].map(world.set_index("year")["co2"]) * 100
    return combined


@pytest.fixture
def dataset(frame):
    countries, regions = split_countries(frame)
    return Dataset(countries=countries, regions=regions)


@pytest.fixture
def countries(dataset):
    return dataset.countries