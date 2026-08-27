"""Manual sanity check against REAL Greenhouse and Lever APIs (no mocking).

Run from backend/: python tests/manual/try_multi_company_scrape.py
"""

from app.sources.greenhouse import GreenhouseJobSource
from app.sources.lever import LeverJobSource
from app.sources.registry import get_source


def try_source(label: str, source, query: str) -> None:
    print(f"\n=== {label} ===")
    postings = source.search(query, limit=5)
    print(f"Found {len(postings)} postings for query {query!r}:")
    for p in postings:
        print(f"- [{p.external_id}] {p.title} | {p.location}")
        print(f"  {p.source_url}")

    if postings:
        full = source.fetch_full_description(postings[0].external_id)
        print(f"\n  Full description for first result ({len(full)} chars):")
        print(f"  {full[:300]}...")


def main() -> None:
    try_source("Greenhouse: Stripe", GreenhouseJobSource("stripe"), "backend engineer")
    try_source("Lever: Palantir", LeverJobSource("palantir"), "software engineer")

    print("\n=== Registry auto-detection ===")
    for company in ["stripe", "palantir", "oracle", "totallynotarealcompanyxyz123"]:
        try:
            source = get_source(company)
            print(f"{company!r} -> {type(source).__name__}")
        except Exception as exc:
            print(f"{company!r} -> error: {exc}")


if __name__ == "__main__":
    main()
