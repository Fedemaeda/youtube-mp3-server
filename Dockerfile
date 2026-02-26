FROM python:3.11-slim

# Install ffmpeg, nodejs, and deno (required for yt-dlp signature bypass)
RUN apt-get update && apt-get install -y ffmpeg nodejs curl unzip && \
    curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/bin/deno && \
    chmod +x /usr/bin/deno && \
    ln -s /usr/bin/nodejs /usr/bin/node || true && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create downloads directory
RUN mkdir -p downloads && chmod 777 downloads

EXPOSE 5000

# Add --remote-components flag to help yt-dlp solve challenges
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app", "--workers", "2", "--timeout", "120"]
