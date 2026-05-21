# Hybrid Setup

Use this mode if:

- `YouTube` should run through your own PC
- `X/Twitter` and `Instagram` should keep using Render

## 1. Start your local YouTube server

Run:

```powershell
.\start_local_youtube_server.ps1
```

That serves ZenRip locally on:

```text
http://127.0.0.1:5005
```

## 2. Expose it with ngrok

In a second terminal, run:

```powershell
.\start_ngrok.ps1
```

Copy the public `https://...ngrok-free.app` URL shown by ngrok.

If you want one command for everything, use:

```powershell
.\start_youtube_public.ps1
```

If ngrok is already running and you only want to print the current public URL, use:

```powershell
.\get_ngrok_url.ps1
```

## 3. Configure the extension

Open the extension settings and set:

- `YouTube Server URL` -> your ngrok URL
- `X / Instagram Server URL` -> `https://youtube-mp3-server-g70t.onrender.com`

## 4. How routing works

- YouTube links -> your local/ngrok server
- X/Twitter links -> Render
- Instagram links -> Render

## Notes

- Keep both the local ZenRip server window and ngrok window open.
- If ngrok gives you a new URL, update only the `YouTube Server URL` in the extension.
- This mode avoids Render's YouTube blocking while preserving your remote server for the other sites.
- If this is your first time using ngrok, authenticate it first with your ngrok account token.
