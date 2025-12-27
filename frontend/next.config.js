/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  
  // For GitHub Pages deployment
  basePath: process.env.NODE_ENV === 'production' ? '/Text-to-Speech' : '',
  
  images: {
    unoptimized: true,
  },
  
  trailingSlash: true,
  
  // Enable experimental features for better static export
  experimental: {
    optimizeCss: true,
  },
}

module.exports = nextConfig
