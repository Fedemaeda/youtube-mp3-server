# Hosting on Hugging Face Spaces (Free & Never Falls)

Hugging Face Spaces is the best free option for this server. It provides 16GB of RAM and runs a Docker container for free.

## Steps to Deploy

1.  **Create a Hugging Face Account**: Go to [huggingface.co](https://huggingface.co/) and sign up.
2.  **Create a New Space**:
    - Click on your profile icon -> **New Space**.
    - **Space Name**: `my-yt-downloader` (or anything you want).
    - **SDK**: Select **Docker**.
    - **Template**: Select **Blank**.
    - **Hardware**: Choose **CPU basic - 2 vCPU - 16 GB - Free**.
    - **Privacy**: **Public** (recommended for ease of use) or **Private**.
3.  **Upload Files**:
    - Click on the **Files and versions** tab.
    - Click **Add file** -> **Upload files**.
    - Drag and drop **all files** from your local project directory EXCEPT `.git`, `downloads/`, and large `.rar`/`.zip` files.
    - **CRITICAL**: Make sure `Dockerfile.hf` is uploaded as `Dockerfile` (rename it during upload or after).
4.  **Wait for Build**: Hugging Face will automatically build and start your server.
5.  **Access your App**: Once the status is **Running**, click on the **App** tab to see your web interface.

## Why this is better than Oracle/Render?
- **No Sleep**: Hugging Face keeps the space warm if it's public.
- **Huge RAM**: 16GB RAM is 32x more than Render's free tier.
- **Latest yt-dlp**: The Dockerfile automatically updates `yt-dlp` to the nightly version for maximum bypass compatibility.
- **PO-Token Support**: It automatically runs `bgutil` in the same container to bypass YouTube blocks.

## Maintenance
If YouTube starts blocking again:
- Go to **Settings** in your Space and click **Factory Reboot** to rebuild with the latest `yt-dlp` fixes.
- Upload a fresh `cookies.txt` via the web interface.
