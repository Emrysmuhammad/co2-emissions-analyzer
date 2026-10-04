import pytest

from emissions import loader
from emissions.loader import Dataset


def test_split_countries_separates_regions(frame):
    countries, regions = loader.split_countries(frame)

    assert set(regions["country"]) == {"World", "Europe"}
    assert "World" not in set(countries["country"])


def test_split_countries_keeps_kosovo_despite_missing_iso_code(frame):
    countries, _ = loader.split_countries(frame)

    assert "Kosovo" in set(countries["country"])


def test_world_property_is_indexed_by_year(dataset):
    assert dataset.world.index.name == "year"
    assert 2020 in dataset.world.index


def test_latest_year_requires_enough_countries(countries):
    assert loader.latest_year(countries, "co2", min_countries=4) == 2020
    assert loader.latest_year(countries, "co2", min_countries=5) == 2015


def test_latest_year_raises_when_no_year_qualifies(countries):
    with pytest.raises(ValueError):
        loader.latest_year(countries, "co2", min_countries=50)


def test_resolve_country_ignores_case_and_accepts_iso_codes(countries):
    assert loader.resolve_country(countries, "  alpha ") == "Alpha"
    assert loader.resolve_country(countries, "bet") == "Beta"


def test_resolve_country_suggests_close_matches(countries):
    with pytest.raises(ValueError, match="Did you mean: Alpha"):
        loader.resolve_country(countries, "Alpah")


def test_resolve_country_rejects_unknown_names(countries):
    with pytest.raises(ValueError, match="Unknown country"):
        loader.resolve_country(countries, "Atlantis")


def test_load_data_reads_a_csv_and_drops_duplicates(frame, tmp_path):
    path = tmp_path / "emissions.csv"
    frame.to_csv(path, index=False)
    with path.open("a", encoding="utf-8") as file:
        file.write(frame.head(1).to_csv(index=False, header=False))

    dataset = loader.load_data(path)

    assert isinstance(dataset, Dataset)
    assert len(dataset.countries) + len(dataset.regions) == len(frame)


def test_load_data_explains_how_to_fix_a_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="python main.py download"):
        loader.load_data(tmp_path / "missing.csv")