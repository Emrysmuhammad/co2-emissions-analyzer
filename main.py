import argparse
import os
import re
import sys
import webbrowser

from emissions import charts, formatting, insight_charts, rankings, trends
from emissions.config import CHART_DIR, METRICS
from emissions.download import download_dataset
from emissions.loader import latest_year, load_data, resolve_country
from emissions.profile import build_profile
from emissions.report import generate_report

MAX_COMPARE = 8


def get_dataset():
    path, downloaded = download_dataset()
    if downloaded:
        print(f"Dataset saved to {path}")
    return load_data(path)


def open_file(path):
    if hasattr(os, "startfile"):
        os.startfile(path)
    else:
        webbrowser.open(path.as_uri())


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def command_download(args):
    path, downloaded = download_dataset(force=args.force)
    if downloaded:
        print(f"Dataset downloaded to {path}")
    else:
        print(f"Dataset already exists at {path} (use --force to download it again)")
    return 0


def command_top(args):
    countries = get_dataset().countries
    year = args.year or latest_year(countries, "co2")

    if args.metric == "co2_per_capita":
        table = rankings.per_capita_leaders(countries, year, args.number)
        specs, title = formatting.PER_CAPITA, "Highest CO2 emissions per person"
    else:
        table = rankings.top_emitters(countries, year, args.number)
        specs, title = formatting.TOP_EMITTERS, "Largest CO2 emitters"

    if table.empty:
        print(f"No data available for {year}.")
        return 1

    print(f"\n{title}, {year}\n")
    print(formatting.text_table(table, specs))
    return 0


def print_profile(profile):
    def ranking(value):
        return f"rank {value[0]} of {value[1]}" if value else "rank n/a"

    print(f"\n{profile['name']} ({profile['year']})\n")
    print(
        f"  Total emissions:  {formatting.whole(profile['co2'])} Mt CO2 "
        f"({formatting.percent(profile['share'])} of world), {ranking(profile['rank'])}"
    )
    print(
        f"  Per person:       {formatting.one_decimal(profile['per_capita'])} tonnes, "
        f"{ranking(profile['per_capita_rank'])}"
    )
    print(f"  Population:       {formatting.millions(profile['population'])} million")

    below_peak = (1 - profile["co2"] / profile["peak"]) * 100
    print(
        f"  Peak:             {formatting.whole(profile['peak'])} Mt in {profile['peak_year']} "
        f"(now {below_peak:.0f}% below)"
    )
    if profile["change_pct"] is not None:
        print(f"  Since {profile['baseline_year']}:       {formatting.signed_percent(profile['change_pct'])}")
    if profile["sources"]:
        ordered = sorted(profile["sources"].items(), key=lambda item: item[1], reverse=True)
        print("  Main sources:     " + ", ".join(f"{label} {share:.0f}%" for label, share in ordered if share >= 1))


def command_country(args):
    dataset = get_dataset()
    name = resolve_country(dataset.countries, args.name)
    print_profile(build_profile(dataset, name))

    slug = slugify(name)
    saved = [charts.plot_trends(dataset.countries, [name], CHART_DIR / f"{slug}-trend.png", start_year=args.since)]
    sources = insight_charts.plot_emission_sources(
        trends.source_mix(dataset.countries, name), name, CHART_DIR / f"{slug}-sources.png"
    )
    if sources:
        saved.append(sources)

    print("\nCharts saved:")
    for path in saved:
        print(f"  {path}")
        if args.open:
            open_file(path)
    return 0


def command_compare(args):
    if len(args.names) > MAX_COMPARE:
        raise ValueError(f"Compare up to {MAX_COMPARE} countries at a time")

    dataset = get_dataset()
    names = [resolve_country(dataset.countries, name) for name in args.names]
    year = latest_year(dataset.countries, "co2")

    rows = dataset.countries[dataset.countries["year"] == year].set_index("country")
    table = rows.reindex(names).reset_index()
    print(f"\nLatest figures ({year})\n")
    print(formatting.text_table(table, formatting.TOP_EMITTERS))

    slugs = "-".join(slugify(name) for name in names)
    path = charts.plot_trends(
        dataset.countries,
        names,
        CHART_DIR / f"compare-{slugs}-{args.metric}.png",
        column=args.metric,
        start_year=args.since,
    )
    print(f"\nChart saved: {path}")
    if args.open:
        open_file(path)
    return 0


def command_report(args):
    path = generate_report(get_dataset(), year=args.year)
    print(f"Report saved: {path}")
    if args.open:
        open_file(path)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Analyze global CO2 emissions with data from Our World in Data.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    download = commands.add_parser("download", help="download the dataset")
    download.add_argument("--force", action="store_true", help="download again even if the file exists")
    download.set_defaults(handler=command_download)

    top = commands.add_parser("top", help="rank countries by emissions")
    top.add_argument("--year", type=int, help="year to rank (default: latest)")
    top.add_argument("-n", "--number", type=int, default=10, help="how many countries to show")
    top.add_argument("--metric", choices=list(METRICS), default="co2")
    top.set_defaults(handler=command_top)

    country = commands.add_parser("country", help="show a profile for one country")
    country.add_argument("name", help="country name or ISO code, e.g. Brazil or BRA")
    country.add_argument("--since", type=int, default=1900, help="first year on the trend chart")
    country.add_argument("--open", action="store_true", help="open the charts when done")
    country.set_defaults(handler=command_country)

    compare = commands.add_parser("compare", help="compare countries on a chart")
    compare.add_argument("names", nargs="+", help="two or more country names or ISO codes")
    compare.add_argument("--metric", choices=list(METRICS), default="co2")
    compare.add_argument("--since", type=int, default=1950, help="first year on the chart")
    compare.add_argument("--open", action="store_true", help="open the chart when done")
    compare.set_defaults(handler=command_compare)

    report = commands.add_parser("report", help="generate the full HTML report")
    report.add_argument("--year", type=int, help="year to analyze (default: latest)")
    report.add_argument("--open", action="store_true", help="open the report when done")
    report.set_defaults(handler=command_report)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except (ValueError, FileNotFoundError, ConnectionError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())