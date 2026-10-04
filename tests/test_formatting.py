import pandas as pd

from emissions import formatting


def test_formatters_show_not_available_for_missing_values():
    assert formatting.whole(float("nan")) == "n/a"
    assert formatting.percent(pd.NA) == "n/a"
    assert formatting.millions(float("nan")) == "n/a"


def test_formatters_round_and_group_numbers():
    assert formatting.whole(12289.037) == "12,289"
    assert formatting.signed_percent(-19.75) == "-20%"
    assert formatting.millions(345_426_571) == "345.4"
    assert formatting.gigatonnes(434_866) == "435"


def test_text_table_aligns_columns_and_handles_empty_tables():
    table = pd.DataFrame({"country": ["China", "India"], "co2": [12289.0, 3193.0]})
    specs = [("country", "Country", formatting.text), ("co2", "Emissions (Mt)", formatting.whole)]

    lines = formatting.text_table(table, specs).splitlines()

    assert lines[0].startswith("Country")
    assert lines[2].endswith("12,289")
    assert len(set(len(line) for line in lines)) == 1
    assert len(formatting.text_table(table.head(0), specs).splitlines()) == 2