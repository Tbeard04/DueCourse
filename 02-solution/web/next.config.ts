import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: the deployed site is plain files — no server, no runtime secrets.
  output: "export",
  // GitHub Pages serves project sites under /<repo>; CI sets this, local builds don't.
  basePath: process.env.PAGES_BASE_PATH ?? "",
  images: { unoptimized: true },
};

export default nextConfig;
