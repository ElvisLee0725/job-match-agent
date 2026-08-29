"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  listJobs,
  parseJobUrl,
  scrapeJobs,
  type JobPostingResponse,
} from "@/lib/api";

const inputClass =
  "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted/70 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition-colors";
const primaryButtonClass =
  "rounded-lg bg-accent text-accent-foreground px-4 py-2 text-sm font-medium hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:hover:bg-accent";
const secondaryButtonClass =
  "rounded-lg border border-border-strong px-4 py-2 text-sm font-medium hover:bg-surface-hover transition-colors disabled:opacity-50";
const cardClass = "rounded-xl border border-border bg-surface p-5";

export default function JobsPage() {
  const [company, setCompany] = useState("oracle");
  const [postings, setPostings] = useState<JobPostingResponse[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const [pasteUrl, setPasteUrl] = useState("");
  const [pasteCompany, setPasteCompany] = useState("");
  const [pasting, setPasting] = useState(false);
  const [pasteError, setPasteError] = useState<string | null>(null);

  useEffect(() => {
    listJobs(company)
      .then(setPostings)
      .catch(() => setPostings([]));
    // only on first load
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setSearching(true);
    setSearchError(null);
    try {
      const results = await scrapeJobs({ company_name: company });
      setPostings(results);
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSearching(false);
    }
  }

  async function handlePasteUrl(e: React.FormEvent) {
    e.preventDefault();
    if (!pasteUrl.trim()) return;
    setPasting(true);
    setPasteError(null);
    try {
      const posting = await parseJobUrl({
        url: pasteUrl.trim(),
        company: pasteCompany.trim() || "unknown",
      });
      setPostings((prev) => [posting, ...prev.filter((p) => p.id !== posting.id)]);
      setPasteUrl("");
    } catch (err) {
      setPasteError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setPasting(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Search open roles</h1>
        <p className="mt-3 text-muted text-sm max-w-xl">
          Search a company&apos;s current open roles using your uploaded profile — works for
          Oracle, plus any company on Greenhouse or Lever. You can also paste a specific
          job posting link (e.g. from LinkedIn) to add it directly.
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1" htmlFor="company">
            Company
          </label>
          <input
            id="company"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className={inputClass}
          />
        </div>
        <button type="submit" disabled={searching} className={primaryButtonClass}>
          {searching ? "Searching..." : "Search"}
        </button>
      </form>
      {searchError && <p className="text-sm text-danger -mt-4">{searchError}</p>}

      <form onSubmit={handlePasteUrl} className={`${cardClass} flex flex-col gap-3`}>
        <h2 className="font-medium text-sm">Paste a specific job posting URL</h2>
        <input
          value={pasteUrl}
          onChange={(e) => setPasteUrl(e.target.value)}
          placeholder="https://www.linkedin.com/jobs/view/..."
          className={inputClass}
        />
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <input
              value={pasteCompany}
              onChange={(e) => setPasteCompany(e.target.value)}
              placeholder="Company name (e.g. oracle)"
              className={inputClass}
            />
          </div>
          <button type="submit" disabled={pasting} className={secondaryButtonClass}>
            {pasting ? "Parsing..." : "Add posting"}
          </button>
        </div>
        {pasteError && <p className="text-sm text-danger">{pasteError}</p>}
      </form>

      <div>
        <h2 className="font-medium mb-3 text-sm text-muted">
          {postings.length} cached posting{postings.length === 1 ? "" : "s"} for &quot;{company}&quot;
        </h2>
        <ul className="flex flex-col gap-3">
          {postings.map((posting) => (
            <li key={posting.id} className={`${cardClass} hover:border-border-strong transition-colors`}>
              <a
                href={posting.source_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium text-accent hover:text-accent-hover transition-colors"
              >
                {posting.title}
              </a>
              <p className="text-sm text-muted mt-0.5">{posting.location ?? "Location not specified"}</p>
              <p className="text-sm text-muted mt-2 line-clamp-3">
                {posting.raw_description}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
