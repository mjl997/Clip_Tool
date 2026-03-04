FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# libpq-dev is for psycopg2 build, gcc is needed for building python packages
# We need to ensure we don't have conflicting packages. 
# Re-installing psycopg2-binary should fix the issue if we have dependencies.
RUN apt-get update && \
    apt-get install -y libpq-dev zip curl gcc build-essential python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Force binary installation for psycopg2 to avoid build issues
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
