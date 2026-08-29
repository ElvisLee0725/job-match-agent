"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  getLatestMatch,
  runMatch,
  type MatchRunResponse,
} from "@/lib/api";

const inputClass =
  "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted/70 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition-colors";
const primaryButtonClass =
  "rounded-lg bg-accent text-accent-foreground px-4 py-2 text-sm font-medium hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:hover:bg-accent";

function scoreClasses(score: number): string {
  if (score >= 75) return "bg-success/15 text-success";
  if (score >= 50) return "bg-warning/15 text-warning";
  return "bg-danger/15 text-danger";
}

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
        <h1 className="text-3xl font-semibold tracking-tight">Your top matches</h1>
        <p className="mt-3 text-muted text-sm max-w-xl">
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
            className={inputClass}
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
            className={`w-24 ${inputClass}`}
          />
        </div>
        <button type="submit" disabled={running} className={primaryButtonClass}>
          {running ? "Ranking..." : "Run match"}
        </button>
      </form>
      {error && <p className="text-sm text-danger -mt-4">{error}</p>}

      {loaded && !matchRun && (
        <p className="text-sm text-muted">No match run yet — click &quot;Run match&quot; above.</p>
      )}

      {matchRun && (
        <div>
          <p className="text-sm text-muted mb-3">
            Last run: {new Date(matchRun.run_at).toLocaleString()}
          </p>
          <ol className="flex flex-col gap-4">
            {matchRun.results.map((pick) => (
              <li
                key={pick.job_posting_id}
                className="rounded-xl border border-border bg-surface p-5 hover:border-border-strong transition-colors"
              >
                <div className="flex items-baseline justify-between gap-4">
                  <a
                    href={pick.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium text-accent hover:text-accent-hover transition-colors"
                  >
                    #{pick.rank} {pick.title}
                  </a>
                  <span
                    className={`text-xs font-semibold whitespace-nowrap rounded-full px-2.5 py-1 ${scoreClasses(pick.fit_score)}`}
                  >
                    {pick.fit_score}/100
                  </span>
                </div>
                <p className="text-sm text-muted mt-0.5">{pick.location ?? "Location not specified"}</p>
                <p className="text-sm mt-3 leading-relaxed">{pick.rationale}</p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}
