"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  getProfile,
  updateProfile,
  uploadProfile,
  type ProfileResponse,
} from "@/lib/api";

function parseStatesText(text: string): string[] {
  return text
    .split(",")
    .map((s) => s.trim().toUpperCase())
    .filter(Boolean);
}

const inputClass =
  "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted/70 focus:outline-none focus:ring-2 focus:ring-accent/40 focus:border-accent transition-colors";
const primaryButtonClass =
  "self-start rounded-lg bg-accent text-accent-foreground px-4 py-2 text-sm font-medium hover:bg-accent-hover transition-colors disabled:opacity-50 disabled:hover:bg-accent";
const cardClass = "rounded-xl border border-border bg-surface p-5 flex flex-col gap-3";

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileResponse | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [backgroundText, setBackgroundText] = useState("");
  const [behavioralAnswers, setBehavioralAnswers] = useState<string[]>([""]);
  const [usOnly, setUsOnly] = useState(true);
  const [preferredStatesText, setPreferredStatesText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);
  const [prefsError, setPrefsError] = useState<string | null>(null);

  useEffect(() => {
    getProfile()
      .then((p) => {
        setProfile(p);
        if (p) {
          setBackgroundText(p.background_text);
          setBehavioralAnswers(p.behavioral_answers.length ? p.behavioral_answers : [""]);
          setUsOnly(p.us_only);
          setPreferredStatesText(p.preferred_states.join(", "));
        }
      })
      .finally(() => setLoaded(true));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!resumeFile) {
      setError("Please choose a resume file (.pdf or .txt).");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const answers = behavioralAnswers.map((a) => a.trim()).filter(Boolean);
      const result = await uploadProfile(
        resumeFile,
        backgroundText,
        answers,
        usOnly,
        parseStatesText(preferredStatesText)
      );
      setProfile(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSaveLocationPrefs() {
    setSavingPrefs(true);
    setPrefsError(null);
    setPrefsSaved(false);
    const startedAt = Date.now();
    try {
      const result = await updateProfile({
        us_only: usOnly,
        preferred_states: parseStatesText(preferredStatesText),
      });
      // This save has no LLM call, so it can finish in well under 100ms — too fast to
      // register as "Saving..." even flashed on screen, which reads as the click doing
      // nothing. Hold the loading state for a minimum stretch so it's actually visible.
      const minVisibleMs = 400;
      const elapsed = Date.now() - startedAt;
      if (elapsed < minVisibleMs) {
        await new Promise((resolve) => setTimeout(resolve, minVisibleMs - elapsed));
      }
      setProfile(result);
      setPrefsSaved(true);
      setTimeout(() => setPrefsSaved(false), 2000);
    } catch (err) {
      setPrefsError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setSavingPrefs(false);
    }
  }

  function updateAnswer(index: number, value: string) {
    setBehavioralAnswers((prev) => prev.map((a, i) => (i === index ? value : a)));
  }

  function addAnswer() {
    setBehavioralAnswers((prev) => [...prev, ""]);
  }

  function removeAnswer(index: number) {
    setBehavioralAnswers((prev) => prev.filter((_, i) => i !== index));
  }

  if (!loaded) {
    return <p className="text-sm text-muted">Loading...</p>;
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Your profile</h1>
        <p className="mt-3 text-muted text-sm">
          {profile
            ? "Uploading a new resume will replace what's stored now."
            : "Upload your resume plus any background notes so we can match you against open roles."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className={`${cardClass} gap-5`}>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="resume_file">
            Resume (.pdf or .txt)
          </label>
          <input
            id="resume_file"
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-accent file:text-accent-foreground file:px-3 file:py-1.5 file:text-sm file:font-medium hover:file:bg-accent-hover file:transition-colors file:cursor-pointer"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="background_text">
            Background notes
          </label>
          <textarea
            id="background_text"
            rows={3}
            value={backgroundText}
            onChange={(e) => setBackgroundText(e.target.value)}
            placeholder="e.g. Looking for senior backend roles at large tech companies, open to relocation."
            className={inputClass}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">
            Sample behavioral answers
          </label>
          <div className="flex flex-col gap-2">
            {behavioralAnswers.map((answer, i) => (
              <div key={i} className="flex gap-2">
                <textarea
                  rows={2}
                  value={answer}
                  onChange={(e) => updateAnswer(i, e.target.value)}
                  placeholder="e.g. Tell me about a conflict with a teammate..."
                  className={`flex-1 ${inputClass}`}
                />
                {behavioralAnswers.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeAnswer(i)}
                    className="text-sm text-muted hover:text-danger transition-colors"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addAnswer}
            className="mt-2 text-sm text-accent hover:text-accent-hover transition-colors"
          >
            + Add another answer
          </button>
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}

        <button type="submit" disabled={loading} className={primaryButtonClass}>
          {loading ? "Uploading..." : profile ? "Update profile" : "Upload profile"}
        </button>
      </form>

      <div className={cardClass}>
        <h2 className="font-medium text-sm">Location preferences</h2>
        <p className="text-sm text-muted">
          Matches outside these preferences are excluded before ranking, not just deprioritized.
        </p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={usOnly}
            onChange={(e) => setUsOnly(e.target.checked)}
            className="accent-accent h-4 w-4"
          />
          US roles only
        </label>
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="preferred_states">
            Preferred states (comma-separated abbreviations, e.g. CA, TX — leave blank for any US state)
          </label>
          <input
            id="preferred_states"
            value={preferredStatesText}
            onChange={(e) => setPreferredStatesText(e.target.value)}
            placeholder="CA, TX"
            className={inputClass}
          />
        </div>
        {prefsError && <p className="text-sm text-danger">{prefsError}</p>}
        {profile && (
          <button
            type="button"
            onClick={handleSaveLocationPrefs}
            disabled={savingPrefs}
            className={primaryButtonClass}
          >
            {savingPrefs ? "Saving..." : prefsSaved ? "Saved ✓" : "Save location preferences"}
          </button>
        )}
        {!profile && (
          <p className="text-sm text-muted">
            These will be saved when you upload your profile above.
          </p>
        )}
      </div>

      {profile && (
        <div className={cardClass}>
          <h2 className="font-medium">Structured profile</h2>
          <dl className="text-sm space-y-3">
            <div>
              <dt className="text-muted text-xs uppercase tracking-wide mb-0.5">Seniority</dt>
              <dd>{profile.structured_profile.seniority || "—"}</dd>
            </div>
            <div>
              <dt className="text-muted text-xs uppercase tracking-wide mb-0.5">Experience</dt>
              <dd>{profile.structured_profile.experience_years} years</dd>
            </div>
            <div>
              <dt className="text-muted text-xs uppercase tracking-wide mb-0.5">Skills</dt>
              <dd>{profile.structured_profile.skills.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt className="text-muted text-xs uppercase tracking-wide mb-0.5">Domains</dt>
              <dd>{profile.structured_profile.domains.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt className="text-muted text-xs uppercase tracking-wide mb-0.5">Summary</dt>
              <dd>{profile.structured_profile.summary || "—"}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
