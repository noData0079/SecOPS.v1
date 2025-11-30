// frontend/next.config.mjs

import { withSentryConfig } from "@sentry/nextjs";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    appDir: true,
  },
};

export default withSentryConfig(
  nextConfig,
  {
    silent: true,
  },
  {
    hideSourceMaps: true,
  }
);
