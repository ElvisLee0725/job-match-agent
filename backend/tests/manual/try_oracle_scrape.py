"""Manual sanity check against the REAL Oracle Recruiting Cloud API (no mocking, no API key
needed — this only exercises the HTTP job-search code, not the LLM matching step).

Run from backend/: python tests/manual/try_oracle_scrape.py
"""

from app.sources.oracle import OracleJobSource


def main() -> None:
    source = OracleJobSource()

    postings = source.search("Senior Python Backend Engineer", limit=10)
    print(f"Found {len(postings)} postings:\n")
    for p in postings:
        print(f"- [{p.external_id}] {p.title} | {p.location}")
        print(f"  {p.source_url}")
        print(f"  {p.raw_description[:150]}...\n")

    if postings:
        full = source.fetch_full_description(postings[0].external_id)
        print("--- full description for first result ---")
        print(full[:1000])


if __name__ == "__main__":
    main()
