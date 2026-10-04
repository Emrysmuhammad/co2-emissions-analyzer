from datetime import date
from html import escape

from emissions import charts, formatting, insight_charts, rankings, trends
from emissions.config import OUTPUT_DIR
from emissions.loader import latest_year

STYLE = """
body { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; color: #1f2937; max-width: 920px; margin: 0 auto; padding: 40px 20px 80px; line-height: 1.6; }
h1 { font-size: 2rem; margin-bottom: 4px; }
h2 { margin-top: 48px; padding-bottom: 8px; border-bottom: 2px solid #e5e7eb; }
.subtitle { color: #6b7280; margin-top: 0; }
.findings { background: #eff6ff; border-left: 4px solid #2563eb; padding: 16px 24px; border-radius: 8px; }
.findings li { margin: 8px 0; }
table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 0.95rem; }
th, td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; text-align: right; }
th:first-child, td:first-child { text-align: left; }
th { background: #f9fafb; font-weight: 600; }
figure { margin: 24px 0; }
img { max-width: 100%; border: 1px solid #e5e7eb; border-radius: 8px; }
figcaption { color: #6b7280; font-size: 0.85rem; margin-top: 6px; }
footer { margin-top: 64px; color: #6b7280; font-size: 0.85rem; }
"""


def table_html(table, specs):
    header = "".join(f"<th>{escape(title)}</th>" for _, title, _ in specs)
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
        for row in formatting.render_rows(table, specs)
    )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"


def figure_html(path, caption, output_dir):
    source = path.relative_to(output_dir).as_posix()
    return (
        f'<figure><img src="{escape(source)}" alt="{escape(caption)}">'
        f"<figcaption>{escape(caption)}</figcaption></figure>"
    )


def findings_html(world, top, per_capita, top_share, peaked, decoupled, income, correlation, gdp_range):
    items = [
        f"Global emissions reached {world['total']:,.0f} million tonnes of CO2 in {world['year']}, "
        f"{world['multiple']:.1f} times the level of {world['baseline_year']}.",
        f"{top.iloc[0]['country']} is the largest emitter with {top.iloc[0]['share_global_co2']:.1f}% of the world total, "
        f"and the five largest emitters together produce {top_share:.0f}%.",
        f"{per_capita.iloc[0]['country']} has the highest emissions per person at "
        f"{per_capita.iloc[0]['co2_per_capita']:.1f} tonnes (countries with over 1 million people).",
        f"{len(peaked)} sizeable emitters have already passed their peak and now emit at least 10% less.",
        f"{len(decoupled)} countries grew their economy while cutting emissions between {gdp_range[0]} and {gdp_range[1]}.",
        f"Across {len(income)} countries, income and emissions per person have a correlation of "
        f"{correlation:.2f} on a log scale.",
    ]
    return "<ul class='findings'>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def generate_report(dataset, output_dir=OUTPUT_DIR, year=None):
    countries = dataset.countries
    year = year or latest_year(countries, "co2")
    if countries.loc[countries["year"] == year, "co2"].notna().sum() < 50:
        raise ValueError(f"Not enough emissions data for {year}")

    gdp_year = latest_year(countries, "gdp")
    since = year - 20
    gdp_since = gdp_year - 20
    chart_dir = output_dir / "charts"

    top = rankings.top_emitters(countries, year, 10)
    per_capita = rankings.per_capita_leaders(countries, year, 10)
    cumulative = rankings.cumulative_emitters(countries, year, 10)
    reducers = trends.biggest_reducers(countries, since, year, 5)
    growers = trends.biggest_growers(countries, since, year, 5)
    peaked = trends.peaked_countries(countries, year)
    decoupled = trends.decoupled_countries(countries, gdp_since, gdp_year)
    income = trends.income_emissions_table(countries, gdp_year)
    correlation = trends.income_emissions_correlation(income)
    world = trends.world_summary(dataset, year)
    leaders = list(top["country"].head(5))

    figures = {
        "top": charts.plot_top_emitters(top, year, chart_dir / "top-emitters.png"),
        "total": charts.plot_trends(countries, leaders, chart_dir / "trends-total.png"),
        "per_capita": charts.plot_trends(
            countries, leaders, chart_dir / "trends-per-capita.png", column="co2_per_capita"
        ),
        "changes": insight_charts.plot_changes(reducers, growers, since, year, chart_dir / "biggest-changes.png"),
        "income": insight_charts.plot_income_vs_emissions(
            income, gdp_year, correlation, chart_dir / "income-vs-emissions.png"
        ),
        "sources": insight_charts.plot_emission_sources(
            trends.source_mix(dataset.regions, "World"), "the world", chart_dir / "world-sources.png"
        ),
    }

    changes = [reducers, growers]
    change_specs = formatting.change_specs(since, year)
    findings = findings_html(
        world,
        top,
        per_capita,
        rankings.top_share(countries, year),
        peaked,
        decoupled,
        income,
        correlation,
        (gdp_since, gdp_year),
    )

    sections = [
        f"<h1>Global CO2 Emissions Report</h1>"
        f"<p class='subtitle'>Data up to {year} &middot; generated {date.today():%B %d, %Y}</p>",
        "<h2>Key findings</h2>" + findings,
        f"<h2>Largest emitters in {year}</h2>"
        + table_html(top, formatting.TOP_EMITTERS)
        + figure_html(figures["top"], f"Ten largest CO2 emitters in {year}", output_dir),
        f"<h2>Emissions per person in {year}</h2>"
        "<p>Countries with more than one million people, ranked by tonnes of CO2 per person.</p>"
        + table_html(per_capita, formatting.PER_CAPITA),
        "<h2>Historical responsibility</h2>"
        "<p>Total emissions since 1750 for the ten largest cumulative emitters.</p>"
        + table_html(cumulative, formatting.CUMULATIVE),
        "<h2>Trends in the five largest emitters</h2>"
        + figure_html(figures["total"], "Annual emissions since 1950", output_dir)
        + figure_html(figures["per_capita"], "Emissions per person since 1950", output_dir),
        f"<h2>Biggest changes since {since}</h2>"
        "<p>Countries with the largest increases and the largest cuts.</p>"
        + table_html(growers, change_specs)
        + table_html(reducers, change_specs)
        + figure_html(figures["changes"], f"Biggest changes in emissions, {since}-{year}", output_dir),
        "<h2>Countries past their peak</h2>"
        "<p>Emitters that peaked at least 10 years ago and now emit at least 10% less.</p>"
        + table_html(peaked.head(15), formatting.PEAKED),
        f"<h2>Growing the economy while cutting emissions</h2>"
        f"<p>Countries whose GDP rose while CO2 emissions fell between {gdp_since} and {gdp_year}.</p>"
        + table_html(decoupled.head(15), formatting.DECOUPLED),
        f"<h2>Income and emissions</h2>"
        + figure_html(figures["income"], f"GDP per person against emissions per person, {gdp_year}", output_dir),
    ]

    if figures["sources"]:
        sections.append(
            "<h2>Where the world's emissions come from</h2>"
            + figure_html(figures["sources"], "Global emissions by source since 1900", output_dir)
        )

    sections.append(
        "<footer>Data: <a href='https://github.com/owid/co2-data'>Our World in Data CO2 dataset</a>, "
        "built on Global Carbon Project data. Emissions are fossil CO2 in million tonnes (Mt).</footer>"
    )

    html = (
        "<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Global CO2 Emissions Report</title><style>{STYLE}</style></head>"
        f"<body>{''.join(sections)}</body></html>"
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    return report_path