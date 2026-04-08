/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {

        protocol: 'https',
        hostname: 'prod.spline.design',
      },
    ],
  },

  output: 'export',      // ← ADD THIS
  trailingSlash: true,
  images: { unoptimized: true },
}

export default nextConfig