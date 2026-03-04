FROM python:3.11-slim

# Install system dependencies (e.g. for audio processing if needed, though faster-whisper handles much)
# Also NVIDIA drivers if we want GPU support in container (base image might need to be nvidia/cuda)
# For CPU inference or simple container, slim is fine. 
# But for GPU, usually: FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04
# I will stick to python:3.11-slim for simplicity and CPU compatibility first, 
# but user mentioned "GPU-intensive".
# Let's use a base that supports both if possible or just stick to python slim and install torch cpu/cuda.
# The user wants "GPU Instance (T4/A10G)", so this Dockerfile should be compatible.
# However, usually development is local (often CPU or no GPU).
# I'll use python:3.11-slim and install dependencies.
# faster-whisper downloads models at runtime or build time.

WORKDIR /app

# Install system dependencies
# PyAV (faster-whisper dependency) needs pkg-config, gcc, and ffmpeg dev libs to build if wheels aren't available
RUN apt-get update && \
    apt-get install -y ffmpeg curl pkg-config build-essential \
    libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev libavfilter-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install torch specifically for CUDA if needed, but requirements.txt has standard torch
# which usually detects CUDA if available.
RUN pip install --no-cache-dir -r requirements.txt

# Create cache directory for models
RUN mkdir -p /root/.cache/huggingface

COPY . .

# Run the service (it will start the API and the background worker)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
