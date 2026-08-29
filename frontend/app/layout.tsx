import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { NavLinks } from "@/components/nav-links";
import { ThemeToggle } from "@/components/theme-toggle";
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

// Runs before hydration so the page never flashes the wrong theme: applies a
// stored explicit choice, or falls back to system preference.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("theme");
    var theme =
      stored === "light" || stored === "dark"
        ? stored
        : window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    document.documentElement.setAttribute("data-theme", theme);
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-full flex flex-col bg-background text-foreground">
        <header className="border-b border-border sticky top-0 z-10 bg-background/80 backdrop-blur-sm">
          <nav className="max-w-3xl mx-auto flex items-center gap-6 px-4 py-3.5">
            <span className="font-semibold tracking-tight flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-accent" />
              Job Match Agent
            </span>
            <NavLinks />
            <ThemeToggle />
          </nav>
        </header>
        <main className="flex-1 max-w-3xl w-full mx-auto px-4 py-10">{children}</main>
      </body>
    </html>
  );
}
