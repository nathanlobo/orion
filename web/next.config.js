/** @type {import('next').NextConfig} */
const nextConfig = {
  // Testing tunnel used to load the dashboard remotely. Without this, Next.js
  // blocks the dev HMR socket (wss://<host>/_next/hmr) as cross-origin.
  // NOTE: next.config.js is read at startup — restart `npm run dev` after changing this.
  allowedDevOrigins: ['test.codinx.app'],
};

module.exports = nextConfig;