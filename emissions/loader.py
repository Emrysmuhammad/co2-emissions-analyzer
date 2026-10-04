import difflib
from dataclasses import dataclass

import pandas as pd

from emissions.config import COLUMNS, DATA_FILE

COUNTRIES_WITHOUT_ISO = {"Kosovo"}


@dataclass(frozen=True)
class Dataset:
    countries: pd.DataFrame
    regions: pd.DataFrame

    @property
    def world(self):
        return self.regions[self.regions["country"] == "World"].set_index("year")


def split_countries(frame):
    is_country = frame["iso_code"].notna() | frame["country"].isin(COUNTRIES_WITHOUT_ISO)
    return frame[is_country].copy(), frame[~is_country].copy()


def load_data(path=DATA_FILE):
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found at {path}. Run: python main.py download")

    frame = pd.read_csv(path, usecols=COLUMNS)
    frame = frame.drop_duplicates(subset=["country", "year"])
    frame = frame.sort_values(["country", "year"]).reset_index(drop=True)
    countries, regions = split_countries(frame)
    return Dataset(countries=countries, regions=regions)


def latest_year(frame, column, min_countries=100):
    counts = frame.dropna(subset=[column]).groupby("year")["country"].nunique()
    years = counts[counts >= min_countries].index
    if len(years) == 0:
        raise ValueError(f"No year has {column} data for at least {min_countries} countries")
    return int(years.max())


def resolve_country(frame, name):
    names = frame.drop_duplicates("country")
    lookup = {row.country.lower(): row.country for row in names.itertuples()}
    for row in names.dropna(subset=["iso_code"]).itertuples():
        lookup.setdefault(row.iso_code.lower(), row.country)

    key = name.strip().lower()
    if key in lookup:
        return lookup[key]

    full_names = [country.lower() for country in names["country"]]
    matches = difflib.get_close_matches(key, full_names, n=3, cutoff=0.7)
    hint = f" Did you mean: {', '.join(lookup[match] for match in matches)}?" if matches else ""
    raise ValueError(f"Unknown country '{name}'.{hint}")