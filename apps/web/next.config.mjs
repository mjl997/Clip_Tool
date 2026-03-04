/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/ingest/:path*",
        destination: "http://ingest-service:8000/api/v1/ingest/:path*",
      },
      {
        source: "/api/v1/transcription/:path*",
        destination: "http://transcription-service:8000/api/v1/transcription/:path*",
      },
      {
        source: "/api/v1/analysis/:path*",
        destination: "http://analysis-service:8000/api/v1/analysis/:path*",
      },
      {
        source: "/api/v1/clips/:path*",
        destination: "http://clipgen-service:8000/api/v1/clips/:path*",
      },
      {
        source: "/api/v1/export/:path*",
        destination: "http://export-service:8000/api/v1/export/:path*",
      },
      {
        source: "/api/v1/jobs",
        destination: "http://export-service:8000/api/v1/jobs",
      },
      {
        source: "/api/v1/jobs/:path*",
        destination: "http://export-service:8000/api/v1/jobs/:path*",
      },
    ];
  },
};

export default nextConfig;
