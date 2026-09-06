import type { NextConfig } from "next";

function normalizeBasePath(value: string | undefined) {
  if (!value || value === "/") return "";
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

const basePath = normalizeBasePath(process.env.NEXT_PUBLIC_BASE_PATH);

const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath,
  assetPrefix: basePath || undefined,
};

export default nextConfig;
