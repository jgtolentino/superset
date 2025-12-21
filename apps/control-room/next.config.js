/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverActions: true,
  },
  env: {
    DATABRICKS_HOST: process.env.DATABRICKS_HOST,
  },
};

module.exports = nextConfig;
