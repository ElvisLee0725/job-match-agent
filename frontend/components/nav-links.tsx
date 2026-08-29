"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_LINKS = [
  { href: "/", label: "Overview" },
  { href: "/profile", label: "Profile" },
  { href: "/jobs", label: "Jobs" },
  { href: "/match", label: "Matches" },
];

export function NavLinks() {
  const pathname = usePathname();

  return (
    <div className="flex gap-1 text-sm">
      {NAV_LINKS.map((link) => {
        const isActive = link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
        return (
          <Link
            key={link.href}
            href={link.href}
            className={`rounded-md px-3 py-1.5 transition-colors ${
              isActive
                ? "bg-accent/15 text-accent font-medium"
                : "text-muted hover:text-foreground hover:bg-surface-hover"
            }`}
          >
            {link.label}
          </Link>
        );
      })}
    </div>
  );
}
