
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:9200/api/:path*',
      },
      {
        source: '/reports/:path*',
        destination: 'http://localhost:9200/reports/:path*',
      },
      {
        source: '/investment_reports/:path*',
        destination: 'http://localhost:9200/investment_reports/:path*',
      },
    ]
  },
};

export default nextConfig;
