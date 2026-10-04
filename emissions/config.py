from pathlib import Path

DATA_URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
CHART_DIR = OUTPUT_DIR / "charts"
DATA_FILE = DATA_DIR / "owid-co2-data.csv"

COLUMNS = [
    "country",
    "year",
    "iso_code",
    "population",
    "gdp",
    "co2",
    "co2_per_capita",
    "cumulative_co2",
    "share_global_co2",
    "coal_co2",
    "oil_co2",
    "gas_co2",
    "cement_co2",
    "flaring_co2",
]

SOURCE_COLUMNS = ["coal_co2", "oil_co2", "gas_co2", "cement_co2", "flaring_co2"]

SOURCE_LABELS = {
    "coal_co2": "Coal",
    "oil_co2": "Oil",
    "gas_co2": "Gas",
    "cement_co2": "Cement",
    "flaring_co2": "Flaring",
}

METRICS = {
    "co2": ("Annual CO2 emissions", "Million tonnes of CO2"),
    "co2_per_capita": ("CO2 emissions per person", "Tonnes of CO2 per person"),
}