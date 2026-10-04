import pytest

from emissions import trends


def test_country_series_respects_start_year(countries):
    series = trends.country_series(countries, "Alpha", "co2", start_year=2015)

    assert series.index.min() == 2015
    assert series.index.max() == 2020


def test_change_between_ignores_countries_below_the_minimum(countries):
    table = trends.change_between(countries, 2000, 2020, min_start_value=10)

    assert "Gamma" not in set(table["country"])
    alpha = table[table["country"] == "Alpha"].iloc[0]
    assert alpha["change"] == pytest.approx(-40)
    assert alpha["change_pct"] == pytest.approx(-10)


def test_biggest_reducers_start_with_the_largest_cut(countries):
    table = trends.biggest_reducers(countries, 2000, 2020, n=2)

    assert list(table["country"]) == ["Alpha", "Delta"]


def test_biggest_growers_start_with_the_largest_increase(countries):
    table = trends.biggest_growers(countries, 2000, 2020, n=1)

    assert list(table["country"]) == ["Beta"]


def test_peaked_countries_finds_emitters_that_have_fallen(countries):
    table = trends.peaked_countries(countries, 2020)

    assert set(table["country"]) == {"Alpha", "Delta"}
    alpha = table[table["country"] == "Alpha"].iloc[0]
    assert alpha["peak_year"] == 2010
    assert alpha["drop_pct"] == pytest.approx(40)


def test_peaked_countries_excludes_recent_peaks(countries):
    table = trends.peaked_countries(countries, 2020, min_years_since_peak=11)

    assert "Alpha" not in set(table["country"])


def test_decoupled_countries_need_growth_and_lower_emissions(countries):
    table = trends.decoupled_countries(countries, 2000, 2020)

    assert set(table["country"]) == {"Alpha", "Delta"}
    assert (table["gdp_change_pct"] > 0).all()
    assert (table["co2_change_pct"] < 0).all()


def test_source_mix_has_one_column_per_source(countries):
    mix = trends.source_mix(countries, "Alpha")

    assert list(mix.columns) == ["coal_co2", "oil_co2", "gas_co2", "cement_co2", "flaring_co2"]
    assert mix.loc[2000].sum() == pytest.approx(400)


def test_income_emissions_table_adds_gdp_per_person(countries):
    table = trends.income_emissions_table(countries, 2020)

    assert "Kosovo" not in set(table["country"])
    alpha = table[table["country"] == "Alpha"].iloc[0]
    assert alpha["gdp_per_capita"] == pytest.approx(2e12 / 100_000_000)


def test_income_emissions_correlation_is_a_valid_coefficient(countries):
    table = trends.income_emissions_table(countries, 2020)

    assert -1 <= trends.income_emissions_correlation(table) <= 1


def test_world_summary_compares_with_the_baseline(dataset):
    summary = trends.world_summary(dataset, 2020, baseline_year=2000)

    assert summary["baseline_year"] == 2000
    assert summary["multiple"] == pytest.approx(summary["total"] / summary["baseline"])