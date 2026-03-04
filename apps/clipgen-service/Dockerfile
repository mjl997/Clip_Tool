FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# ffmpeg for video processing, libgl1/libglib2.0 for opencv
RUN apt-get update && \
    apt-get install -y ffmpeg libgl1 libglib2.0-0 fonts-noto fonts-liberation fontconfig && \
    rm -rf /var/lib/apt/lists/*

# Setup fonts for subtitles
# We might want to copy custom fonts here if needed
RUN fc-cache -f -v

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
