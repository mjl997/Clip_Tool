# Clip Tool - Monorepo

## Prerequisites

- Docker & Docker Compose
- Node.js & pnpm (optional, for local task running)
- Python 3.11+ (optional, for local development)

## Getting Started

1.  **Start Infrastructure & Services**:
    ```bash
    docker-compose up --build
    ```

2.  **Verify Services**:
    - **Traefik Dashboard**: [http://localhost:8080](http://localhost:8080)
    - **Core Service Health**: [http://localhost:8000/health](http://localhost:8000/health) (Direct) or [http://localhost/api/core/health](http://localhost/api/core/health) (Via Gateway)
    - **Ingest Service**: [http://localhost/api/v1/ingest/health](http://localhost/api/v1/ingest/health)
    - **Transcription Service**: [http://localhost/api/v1/transcription/health](http://localhost/api/v1/transcription/health)
    - **Analysis Service**: [http://localhost/api/v1/analysis/health](http://localhost/api/v1/analysis/health)
    - **ClipGen Service**: [http://localhost/api/v1/clips/health](http://localhost/api/v1/clips/health)
    - **Export Service**: [http://localhost/api/v1/export/health](http://localhost/api/v1/export/health)
    - **Frontend**: [http://localhost:3000](http://localhost:3000)
    - **MinIO Console**: [http://localhost:9001](http://localhost:9001) (user/password)

3.  **Database Migrations**:
    To create an initial migration:
    ```bash
    docker-compose run --rm core-service alembic revision --autogenerate -m "Initial migration"
    ```
    To apply migrations:
    ```bash
    docker-compose run --rm core-service alembic upgrade head
    ```

## Usage (Web UI)

1.  Open [http://localhost:3000](http://localhost:3000) in your browser.
2.  Paste a YouTube URL and click **Process**.
3.  Watch the progress bar as the system ingests, transcribes, analyzes, and generates clips.
4.  Once complete, browse the viral clips grid.
5.  Click **MP4** to download individual clips or **Download All (ZIP)** for the full batch.
6.  Use the **Settings** page to configure API keys or preferences.

## Usage (API)

### 1. Submit a Video
```bash
curl -X POST "http://localhost/api/v1/ingest" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### 2. Monitor & List Jobs
```bash
curl "http://localhost/api/v1/jobs?limit=5"
```
Returns a list of recent jobs with status.

### 3. Download Clips (Export)
Once a job is `completed` (clips generated), you can download files.

**Download Single Clip:**
```bash
curl -O -J "http://localhost/api/v1/export/{job_id}/{clip_id}?format=mp4_subs"
```

**Download All (ZIP):**
```bash
curl -O -J "http://localhost/api/v1/export/{job_id}/all"
```

## Production Deployment

### 1. Configure Environment
Create a `.env.prod` file with your secrets:
```bash
POSTGRES_PASSWORD=secure_password
MINIO_ROOT_PASSWORD=secure_password
GRAFANA_PASSWORD=secure_password
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Deploy with HTTPS
Use the production compose file which enables Let's Encrypt and Monitoring:

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 3. Monitoring
Access the monitoring stack:
- **Grafana**: `http://your-domain:3001` (Default user: admin)
- **Prometheus**: `http://your-domain:9090`
- **Traefik Dashboard**: `http://your-domain:8080`

## Testing

### End-to-End Test
Run the E2E test script to verify the entire pipeline:

```bash
python tests/e2e.py --url "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

## Project Structure

- `apps/`
    - `core-service`: Python FastAPI service with Alembic migrations.
    - `ingest-service`: Video ingestion service (yt-dlp, MinIO, Redis).
    - `transcription-service`: Whisper-based transcription (faster-whisper, GPU/CPU).
    - `analysis-service`: Virality analysis using LLM (OpenAI/Anthropic) & Audio features.
    - `clipgen-service`: Smart cutting, cropping (MediaPipe), and subtitling (FFmpeg).
    - `export-service`: Downloads, ZIP generation, job history, and auto-cleanup.
    - `web`: Next.js frontend UI.
    - `gateway`: Traefik configuration (in docker-compose).
- `packages/`: Shared libraries (Logger, Queue).
- `docker-compose.yml`: Local development.
- `docker-compose.prod.yml`: Production deployment (HTTPS, Monitoring).
- `tests/`: E2E and integration tests.
