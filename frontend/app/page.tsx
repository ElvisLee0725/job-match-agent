"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getProfile, type ProfileResponse } from "@/lib/api";

const STEPS = [
  {
    n: 1,
    title: "Your profile",
    href: "/profile",
  },
  {
    n: 2,
    title: "Search a company's open roles",
    body: "Works for Oracle, plus any company on Greenhouse or Lever — just type their name. You can also paste a link to any specific job posting.",
    href: "/jobs",
    cta: "Go to Jobs",
  },
  {
    n: 3,
    title: "Get your top matches",
    body: "Once you have a profile and some searched jobs, run the match to see your best fits.",
    href: "/match",
    cta: "Go to Matches",
  },
];

export default function OverviewPage() {
  const [profile, setProfile] = useState<ProfileResponse | null | undefined>(undefined);

  useEffect(() => {
    getProfile().then(setProfile).catch(() => setProfile(null));
  }, []);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Job Match Agent</h1>
        <p className="mt-3 text-muted max-w-xl">
          Upload your background once, then search a company&apos;s open roles and get your
          best-fitting positions, ranked with a plain-language explanation of why.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="rounded-xl border border-border bg-surface p-5">
          <div className="flex items-center gap-2 mb-2">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent text-xs font-semibold">
              1
            </span>
            <h2 className="font-medium">Your profile</h2>
          </div>
          {profile === undefined && <p className="text-sm text-muted pl-7">Checking...</p>}
          {profile === null && (
            <p className="text-sm text-muted pl-7">
              No profile uploaded yet.{" "}
              <Link href="/profile" className="text-accent hover:text-accent-hover">
                Upload your resume
              </Link>{" "}
              to get started.
            </p>
          )}
          {profile && (
            <div className="text-sm pl-7 space-y-1">
              <p>
                <span className="font-medium">{profile.structured_profile.seniority}</span>{" "}
                <span className="text-muted">
                  &middot; {profile.structured_profile.experience_years} years
                </span>
              </p>
              <p className="text-muted">
                {profile.structured_profile.skills.slice(0, 6).join(", ")}
                {profile.structured_profile.skills.length > 6 ? ", ..." : ""}
              </p>
              <Link href="/profile" className="text-accent hover:text-accent-hover inline-block mt-1">
                Edit profile
              </Link>
            </div>
          )}
        </div>

        {STEPS.slice(1).map((step) => (
          <div key={step.n} className="rounded-xl border border-border bg-surface p-5">
            <div className="flex items-center gap-2 mb-2">
              <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent/15 text-accent text-xs font-semibold">
                {step.n}
              </span>
              <h2 className="font-medium">{step.title}</h2>
            </div>
            <p className="text-sm text-muted pl-7">{step.body}</p>
            <Link href={step.href} className="text-sm text-accent hover:text-accent-hover pl-7 inline-block mt-1">
              {step.cta}
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
