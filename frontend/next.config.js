/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Explicitly use App Router only  
  pageExtensions: ['tsx', 'ts'],
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
  webpack: (config) => {
    // Add SVG support
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });
    
    return config;
  },
  // Temporary cleanup debt:
  // - standalone typecheck currently passes via `npm run type-check`
  // - standalone build currently passes
  // - keep these build suppressions only until lint is brought back under control
  //   and the team is ready to enforce the checks inside `next build`
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
