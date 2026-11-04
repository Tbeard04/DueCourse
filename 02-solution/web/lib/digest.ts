export interface DigestItem {
  companyName: string;
  companyNumber: string;
  filing: string;
  /** ISO date, e.g. "2026-11-06" */
  dueDate: string;
  /** Negative when overdue, 0 when due today. */
  daysUntilDue: number;
}

export type SectionSlug = "overdue" | "due-soon" | "upcoming" | "ok";

export interface DigestSection {
  slug: SectionSlug;
  label: string;
  items: DigestItem[];
}

export interface Digest {
  /** Preformatted in the Python exporter, e.g. "03 November 2026". */
  asOf: string;
  /** Preformatted UTC timestamp of the export run. */
  generated: string;
  portfolioSize: number;
  sections: DigestSection[];
}

export function daysPhrase(days: number): string {
  if (days < 0) return `${-days} day${days !== -1 ? "s" : ""} overdue`;
  if (days === 0) return "due today";
  return `in ${days} day${days !== 1 ? "s" : ""}`;
}

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
] as const;

/** "2026-11-06" -> "06 Nov 2026" — fixed mapping so build and hydration agree exactly. */
export function formatDueDate(iso: string): string {
  const [year, month, day] = iso.split("-").map(Number);
  return `${String(day).padStart(2, "0")} ${MONTHS[month - 1]} ${year}`;
}
