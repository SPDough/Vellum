import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Explicitly use App Router only
  pageExtensions: ['tsx', 'ts'],
  output: 'standalone',
  // Pin app root so a parent package-lock.json (repo root) does not break @/ aliases on Vercel.
  outputFileTracingRoot: __dirname,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      '@': path.join(__dirname, 'src'),
      '@components': path.join(__dirname, 'src/components'),
      '@pages': path.join(__dirname, 'src/pages'),
      '@hooks': path.join(__dirname, 'src/hooks'),
      '@utils': path.join(__dirname, 'src/utils'),
      '@types': path.join(__dirname, 'src/types'),
      '@store': path.join(__dirname, 'src/store'),
      '@assets': path.join(__dirname, 'src/assets'),
    };

    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });

    return config;
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
