import type { NextConfig } from "next";

const isGitHubActions = process.env.GITHUB_ACTIONS === "true";
const repoName = process.env.GITHUB_REPOSITORY?.split("/")[1] ?? "";
const repoOwner = process.env.GITHUB_REPOSITORY_OWNER ?? "";
const isUserSite =
  repoName !== "" && repoOwner !== "" && repoName.toLowerCase() === `${repoOwner.toLowerCase()}.github.io`;
const basePath = isGitHubActions && repoName && !isUserSite ? `/${repoName}` : "";

const nextConfig: NextConfig = {
  reactCompiler: true,
  output: "export",
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath,
  assetPrefix: basePath || undefined,
};

export default nextConfig;
