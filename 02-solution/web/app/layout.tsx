import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DueCourse — weekly filing digest",
  description:
    "Weekly Companies House filing digest for a demo accountancy portfolio — " +
    "deadlines triaged deterministically from the live public register.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en-GB">
      <body>{children}</body>
    </html>
  );
}
