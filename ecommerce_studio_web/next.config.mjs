/** @type {import('next').NextConfig} */
const nextConfig = {
  // 由 Next.js App Router API Route Handler 原生网关转发，解除 http-proxy 硬编码 30s 超时限制
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
