FROM python:3.11-slim

# Install ffmpeg which is required by yt-dlp to extract MP3s
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Run the application with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--timeout", "120", "--workers", "2", "app:app"]
