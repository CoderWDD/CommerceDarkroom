/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/v1/studio/:path*',
        destination: `${process.env.FASTAPI_BACKEND_URL || 'http://127.0.0.1:8000'}/api/v1/studio/:path*`,
      },
      {
        source: '/output/:path*',
        destination: `${process.env.FASTAPI_BACKEND_URL || 'http://127.0.0.1:8000'}/output/:path*`,
      },
    ];
  },
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
