import shutil
import urllib.request
from urllib.error import URLError

from emissions.config import DATA_FILE, DATA_URL


def download_dataset(force=False):
    if DATA_FILE.exists() and not force:
        return DATA_FILE, False

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    partial = DATA_FILE.with_suffix(".part")
    request = urllib.request.Request(DATA_URL, headers={"User-Agent": "co2-emissions-analysis"})

    try:
        with urllib.request.urlopen(request, timeout=60) as response, open(partial, "wb") as target:
            shutil.copyfileobj(response, target)
    except (URLError, TimeoutError) as error:
        partial.unlink(missing_ok=True)
        raise ConnectionError(f"Could not download the dataset: {error}") from error

    partial.replace(DATA_FILE)
    return DATA_FILE, True