"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  listJobs,
  parseJobUrl,
  scrapeJobs,
  type JobPostingResponse,
} from "@/lib/api";

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
        <h1 className="text-2xl font-semibold">Search open roles</h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400 text-sm">
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
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={searching}
          className="rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {searching ? "Searching..." : "Search"}
        </button>
      </form>
      {searchError && <p className="text-sm text-red-600 -mt-4">{searchError}</p>}

      <form onSubmit={handlePasteUrl} className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4 flex flex-col gap-3">
        <h2 className="font-medium text-sm">Paste a specific job posting URL</h2>
        <input
          value={pasteUrl}
          onChange={(e) => setPasteUrl(e.target.value)}
          placeholder="https://www.linkedin.com/jobs/view/..."
          className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
        />
        <div className="flex gap-2 items-end">
          <div className="flex-1">
            <input
              value={pasteCompany}
              onChange={(e) => setPasteCompany(e.target.value)}
              placeholder="Company name (e.g. oracle)"
              className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
            />
          </div>
          <button
            type="submit"
            disabled={pasting}
            className="rounded border border-neutral-300 dark:border-neutral-700 px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {pasting ? "Parsing..." : "Add posting"}
          </button>
        </div>
        {pasteError && <p className="text-sm text-red-600">{pasteError}</p>}
      </form>

      <div>
        <h2 className="font-medium mb-3">
          {postings.length} cached posting{postings.length === 1 ? "" : "s"} for &quot;{company}&quot;
        </h2>
        <ul className="flex flex-col gap-3">
          {postings.map((posting) => (
            <li
              key={posting.id}
              className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4"
            >
              <a
                href={posting.source_url}
                target="_blank"
                rel="noreferrer"
                className="font-medium underline"
              >
                {posting.title}
              </a>
              <p className="text-sm text-neutral-500">{posting.location ?? "Location not specified"}</p>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1 line-clamp-3">
                {posting.raw_description}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
