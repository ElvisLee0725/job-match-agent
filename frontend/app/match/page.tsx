"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  getLatestMatch,
  runMatch,
  type MatchRunResponse,
} from "@/lib/api";

export default function MatchPage() {
  const [company, setCompany] = useState("oracle");
  const [topN, setTopN] = useState(3);
  const [matchRun, setMatchRun] = useState<MatchRunResponse | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getLatestMatch(company)
      .then(setMatchRun)
      .finally(() => setLoaded(true));
    // only on first load
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleRun(e: React.FormEvent) {
    e.preventDefault();
    setRunning(true);
    setError(null);
    try {
      const result = await runMatch({ company_name: company, top_n: topN });
      setMatchRun(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold">Your top matches</h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400 text-sm">
          Ranks your cached postings for a company against your profile and picks the best
          matches. Make sure you&apos;ve uploaded a profile and searched a company first.
        </p>
      </div>

      <form onSubmit={handleRun} className="flex gap-2 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium mb-1" htmlFor="match_company">
            Company
          </label>
          <input
            id="match_company"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="match_top_n">
            # of matches
          </label>
          <input
            id="match_top_n"
            type="number"
            min={1}
            max={20}
            value={topN}
            onChange={(e) => setTopN(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
            className="w-24 rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        <button
          type="submit"
          disabled={running}
          className="rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {running ? "Ranking..." : "Run match"}
        </button>
      </form>
      {error && <p className="text-sm text-red-600 -mt-4">{error}</p>}

      {loaded && !matchRun && (
        <p className="text-sm text-neutral-500">No match run yet — click &quot;Run match&quot; above.</p>
      )}

      {matchRun && (
        <div>
          <p className="text-sm text-neutral-500 mb-3">
            Last run: {new Date(matchRun.run_at).toLocaleString()}
          </p>
          <ol className="flex flex-col gap-4">
            {matchRun.results.map((pick) => (
              <li
                key={pick.job_posting_id}
                className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <a
                    href={pick.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium underline"
                  >
                    #{pick.rank} {pick.title}
                  </a>
                  <span className="text-sm font-medium text-neutral-500 whitespace-nowrap">
                    {pick.fit_score}/100
                  </span>
                </div>
                <p className="text-sm text-neutral-500">{pick.location ?? "Location not specified"}</p>
                <p className="text-sm text-neutral-700 dark:text-neutral-300 mt-2">{pick.rationale}</p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
