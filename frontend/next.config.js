/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8282/api/:path*', // Proxy to Backend
      },
      // Note: WebSocket connections can't be proxied through Next.js rewrites
      // WebSocket connections will be made directly to the backend
    ]
  },
}

module.exports = nextConfig
