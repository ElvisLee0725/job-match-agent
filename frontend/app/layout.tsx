import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Job Match Agent",
  description: "Find your best-fitting open roles at a company, ranked by fit.",
};

const NAV_LINKS = [
  { href: "/", label: "Overview" },
  { href: "/profile", label: "Profile" },
  { href: "/jobs", label: "Jobs" },
  { href: "/match", label: "Matches" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
        <header className="border-b border-neutral-200 dark:border-neutral-800">
          <nav className="max-w-3xl mx-auto flex items-center gap-6 px-4 py-4">
            <span className="font-semibold">Job Match Agent</span>
            <div className="flex gap-4 text-sm">
              {NAV_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </nav>
        </header>
        <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
