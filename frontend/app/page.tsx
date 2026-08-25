"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getProfile, type ProfileResponse } from "@/lib/api";

export default function OverviewPage() {
  const [profile, setProfile] = useState<ProfileResponse | null | undefined>(undefined);

  useEffect(() => {
    getProfile().then(setProfile).catch(() => setProfile(null));
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold">Job Match Agent</h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400">
          Upload your background once, then search a company&apos;s open roles and get your
          top 3 best-fitting positions, ranked with a plain-language explanation of why.
        </p>
      </div>

      <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4">
        <h2 className="font-medium mb-2">1. Your profile</h2>
        {profile === undefined && (
          <p className="text-sm text-neutral-500">Checking...</p>
        )}
        {profile === null && (
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            No profile uploaded yet.{" "}
            <Link href="/profile" className="underline">
              Upload your resume
            </Link>{" "}
            to get started.
          </p>
        )}
        {profile && (
          <div className="text-sm text-neutral-700 dark:text-neutral-300 space-y-1">
            <p>
              <span className="font-medium">{profile.structured_profile.seniority}</span>{" "}
              &middot; {profile.structured_profile.experience_years} years
            </p>
            <p className="text-neutral-500">
              {profile.structured_profile.skills.slice(0, 6).join(", ")}
              {profile.structured_profile.skills.length > 6 ? ", ..." : ""}
            </p>
            <Link href="/profile" className="underline">
              Edit profile
            </Link>
          </div>
        )}
      </div>

      <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4">
        <h2 className="font-medium mb-2">2. Search a company&apos;s open roles</h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Currently supported: Oracle. You can also paste a link to any specific job posting.
        </p>
        <Link href="/jobs" className="underline text-sm">
          Go to Jobs
        </Link>
      </div>

      <div className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4">
        <h2 className="font-medium mb-2">3. Get your top 3 matches</h2>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          Once you have a profile and some searched jobs, run the match to see your best fits.
        </p>
        <Link href="/match" className="underline text-sm">
          Go to Matches
        </Link>
      </div>
    </div>
  );
}
