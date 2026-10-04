import pytest

from emissions import rankings


def test_top_emitters_are_sorted_from_largest_to_smallest(countries):
    table = rankings.top_emitters(countries, 2020, n=3)

    assert list(table["country"]) == ["Alpha", "Beta", "Delta"]
    assert table["co2"].is_monotonic_decreasing


def test_top_emitters_respects_the_requested_count(countries):
    assert len(rankings.top_emitters(countries, 2020, n=2)) == 2


def test_top_emitters_is_empty_for_a_year_without_data(countries):
    assert rankings.top_emitters(countries, 1850).empty


def test_per_capita_leaders_skip_small_populations_by_default(countries):
    table = rankings.per_capita_leaders(countries, 2020)

    assert "Gamma" not in set(table["country"])
    assert table.iloc[0]["country"] == "Beta"


def test_per_capita_leaders_can_include_small_populations(countries):
    table = rankings.per_capita_leaders(countries, 2020, min_population=0)

    assert "Gamma" in set(table["country"])


def test_cumulative_emitters_report_shares_that_add_up(countries):
    table = rankings.cumulative_emitters(countries, 2020, n=10)

    assert table.iloc[0]["country"] == "Alpha"
    assert table["share"].sum() == pytest.approx(100)


def test_country_rank_returns_position_and_total(countries):
    assert rankings.country_rank(countries, "Beta", 2020) == (2, 4)


def test_country_rank_is_none_for_unknown_country(countries):
    assert rankings.country_rank(countries, "Atlantis", 2020) is None


def test_top_share_of_a_single_country(countries):
    rows = countries[countries["year"] == 2020]
    expected = rows["co2"].max() / rows["co2"].sum() * 100

    assert rankings.top_share(countries, 2020, top_n=1) == pytest.approx(expected)