---
title: ZenRip
emoji: "⬇️"
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 5000
---

# ZenRip

ZenRip is a Flask + `yt-dlp` downloader for YouTube, X/Twitter, and Instagram.

## Recommended hosting

This repo is ready for either:

- Hugging Face Spaces with Docker
- Render web service with Docker

## Hugging Face Spaces

1. Create a new Space and choose `Docker`.
2. Import this GitHub repository or upload the repo contents.
3. The Space should use port `5000` from this repo metadata.
4. Wait for the Docker build to finish.
5. Open your public URL: `https://<your-space>.hf.space/`

## Render

1. Create a new `Web Service`.
2. Connect this GitHub repository.
3. Use `Docker` runtime.
4. Keep `FLASK_ENV=production`.
5. After deploy, use your public URL: `https://<your-service>.onrender.com/`

## Extension

After deployment, open the extension settings and set the server URL to your public domain, for example:

- `https://<your-space>.hf.space`
- `https://<your-service>.onrender.com`
