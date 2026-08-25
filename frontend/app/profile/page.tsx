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
    try {
      const result = await updateProfile({
        us_only: usOnly,
        preferred_states: parseStatesText(preferredStatesText),
      });
      setProfile(result);
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
    return <p className="text-sm text-neutral-500">Loading...</p>;
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold">Your profile</h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400 text-sm">
          {profile
            ? "Uploading a new resume will replace what's stored now."
            : "Upload your resume plus any background notes so we can match you against open roles."}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="resume_file">
            Resume (.pdf or .txt)
          </label>
          <input
            id="resume_file"
            type="file"
            accept=".pdf,.txt"
            onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
            className="block w-full text-sm file:mr-3 file:rounded file:border-0 file:bg-neutral-900 file:text-white file:px-3 file:py-1.5 dark:file:bg-neutral-100 dark:file:text-neutral-900"
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
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
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
                  className="flex-1 rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
                />
                {behavioralAnswers.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeAnswer(i)}
                    className="text-sm text-neutral-500 hover:text-red-600"
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
            className="mt-2 text-sm underline text-neutral-600 dark:text-neutral-400"
          >
            + Add another answer
          </button>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="self-start rounded bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900 px-4 py-2 text-sm font-medium disabled:opacity-50"
        >
          {loading ? "Uploading..." : profile ? "Update profile" : "Upload profile"}
        </button>
      </form>

      <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4 flex flex-col gap-3">
        <h2 className="font-medium text-sm">Location preferences</h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Matches outside these preferences are excluded before ranking, not just deprioritized.
        </p>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={usOnly}
            onChange={(e) => setUsOnly(e.target.checked)}
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
            className="w-full rounded border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm"
          />
        </div>
        {prefsError && <p className="text-sm text-red-600">{prefsError}</p>}
        {profile && (
          <button
            type="button"
            onClick={handleSaveLocationPrefs}
            disabled={savingPrefs}
            className="self-start rounded border border-neutral-300 dark:border-neutral-700 px-4 py-2 text-sm font-medium disabled:opacity-50"
          >
            {savingPrefs ? "Saving..." : "Save location preferences"}
          </button>
        )}
        {!profile && (
          <p className="text-sm text-neutral-500">
            These will be saved when you upload your profile above.
          </p>
        )}
      </div>

      {profile && (
        <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4">
          <h2 className="font-medium mb-2">Structured profile</h2>
          <dl className="text-sm space-y-2">
            <div>
              <dt className="text-neutral-500">Seniority</dt>
              <dd>{profile.structured_profile.seniority || "—"}</dd>
            </div>
            <div>
              <dt className="text-neutral-500">Experience</dt>
              <dd>{profile.structured_profile.experience_years} years</dd>
            </div>
            <div>
              <dt className="text-neutral-500">Skills</dt>
              <dd>{profile.structured_profile.skills.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt className="text-neutral-500">Domains</dt>
              <dd>{profile.structured_profile.domains.join(", ") || "—"}</dd>
            </div>
            <div>
              <dt className="text-neutral-500">Summary</dt>
              <dd>{profile.structured_profile.summary || "—"}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
