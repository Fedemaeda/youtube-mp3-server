document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('youtube-url');
    const downloadBtn = document.getElementById('download-btn');
    const downloadMp4Btn = document.getElementById('download-mp4-btn');
    const statusMessage = document.getElementById('status-message');
    const settingsBtn = document.getElementById('settings-btn');
    const serverBadge = document.getElementById('server-badge');

    let youtubeServerUrl = '';
    let socialServerUrl = '';
    let activeMediaType = null;

    chrome.storage.sync.get(['serverUrl', 'youtubeServerUrl', 'socialServerUrl'], (result) => {
        const legacyUrl = (result.serverUrl || '').replace(/\/$/, '');
        youtubeServerUrl = (result.youtubeServerUrl || '').replace(/\/$/, '');
        socialServerUrl = (result.socialServerUrl || legacyUrl).replace(/\/$/, '');
        chrome.tabs.query({ active: true, currentWindow: true }, handleActiveTab);
    });

    function handleActiveTab(tabs) {
        const activeTab = tabs[0];
        const currentUrl = activeTab?.url || '';
        const mediaType = detectMediaType(currentUrl);
        activeMediaType = mediaType;

        if (mediaType) {
            urlInput.value = currentUrl;
            updateServerBadge(mediaType);
            return;
        }

        urlInput.value = '';
        urlInput.placeholder = 'No supported video found';
        downloadBtn.disabled = true;
        downloadMp4Btn.disabled = true;
        urlInput.classList.add('disabled');
        setServerStatus('Unsupported page', 'error');
    }

    function detectMediaType(url) {
        if (url.includes('youtube.com/watch') || url.includes('youtu.be/')) {
            return 'youtube';
        }
        if (url.includes('x.com/') || url.includes('twitter.com/')) {
            return 'social';
        }
        if (
            url.includes('instagram.com/p/') ||
            url.includes('instagram.com/reels/') ||
            url.includes('instagram.com/reel/') ||
            url.includes('instagram.com/tv/')
        ) {
            return 'social';
        }
        return null;
    }

    function getServerUrl(mediaType) {
        return mediaType === 'youtube' ? youtubeServerUrl : socialServerUrl;
    }

    function describeServer(mediaType) {
        return mediaType === 'youtube' ? 'YouTube -> Local' : 'X/Instagram -> Render';
    }

    async function updateServerBadge(mediaType) {
        const serverUrl = getServerUrl(mediaType);
        if (!serverUrl) {
            const missingLabel = mediaType === 'youtube' ? 'Set local YouTube URL' : 'Set Render URL';
            setServerStatus(missingLabel, 'info');
            return;
        }

        try {
            const resp = await fetch(`${serverUrl}/api/cookies-status`);
            if (resp.ok) {
                const data = await resp.json();
                const suffix = data.has_cookies ? 'Ready' : 'Online';
                setServerStatus(`${describeServer(mediaType)}: ${suffix}`, data.has_cookies ? 'success' : 'info');
                return;
            }
        } catch (error) {
            console.warn('Server unreachable', error);
        }

        setServerStatus(`${describeServer(mediaType)}: Offline`, 'error');
    }

    function setServerStatus(message, type) {
        serverBadge.textContent = message;
        serverBadge.className = `server-badge ${type}`;
    }

    function setStatus(message, type) {
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.opacity = '0';
        setTimeout(() => {
            statusMessage.style.opacity = '1';
        }, 10);
    }

    function getCookiesForDomain(url) {
        const domain = new URL(url).hostname;
        const baseDomain = domain.split('.').slice(-2).join('.');
        return new Promise((resolve) => {
            chrome.cookies.getAll({ domain: baseDomain }, (cookies) => {
                resolve(cookies);
            });
        });
    }

    async function syncCookies(url, serverUrl) {
        try {
            setStatus('Synchronizing session...', 'info');
            const cookies = await getCookiesForDomain(url);
            if (!cookies || cookies.length === 0) {
                return false;
            }

            const resp = await fetch(`${serverUrl}/api/sync-cookies-json`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookies })
            });

            if (!resp.ok) {
                throw new Error('Sync failed server-side');
            }

            const data = await resp.json();
            return data.success;
        } catch (error) {
            console.warn('Cookie sync failed:', error);
            return false;
        }
    }

    async function handleDownload(format, btn) {
        const url = urlInput.value;
        if (!url || !activeMediaType) {
            return;
        }

        const serverUrl = getServerUrl(activeMediaType);
        if (!serverUrl || !/^https?:\/\//i.test(serverUrl)) {
            const configMessage = activeMediaType === 'youtube'
                ? 'Configure your local YouTube server URL first.'
                : 'Configure your Render server URL first.';
            setStatus(configMessage, 'error');
            return;
        }

        const btnText = btn.querySelector('.btn-text');
        const spinner = btn.querySelector('.spinner');
        downloadBtn.disabled = true;
        downloadMp4Btn.disabled = true;
        btnText.style.display = 'none';
        spinner.style.display = 'block';

        try {
            const validateResp = await fetch(`${serverUrl}/api/validate-url`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            if (!validateResp.ok) {
                let message = 'Invalid URL';
                try {
                    const data = await validateResp.json();
                    message = data.error || message;
                } catch (error) {
                    console.warn(error);
                }
                setStatus(message, 'error');
                resetBtns();
                return;
            }

            await syncCookies(url, serverUrl);
            setStatus(`Processing ${format.toUpperCase()}...`, 'info');

            const getUrl = new URL(`${serverUrl}/api/download`);
            getUrl.searchParams.append('url', url);
            getUrl.searchParams.append('format', format);

            chrome.downloads.download({
                url: getUrl.toString(),
                saveAs: false,
                headers: [
                    { name: 'X-Client-Type', value: 'ZenRip-Extension' }
                ]
            }, (downloadId) => {
                if (chrome.runtime.lastError) {
                    console.error(chrome.runtime.lastError);
                    setStatus(chrome.runtime.lastError.message, 'error');
                    resetBtns();
                    return;
                }

                setStatus('Requesting file...', 'info');

                const listener = (delta) => {
                    if (delta.id !== downloadId || !delta.state) {
                        return;
                    }

                    if (delta.state.current === 'complete') {
                        setStatus('Download complete!', 'success');
                        chrome.downloads.onChanged.removeListener(listener);
                        setTimeout(() => {
                            resetBtns();
                            window.close();
                        }, 2500);
                    } else if (delta.state.current === 'interrupted') {
                        setStatus('Download failed (Interrupted)', 'error');
                        chrome.downloads.onChanged.removeListener(listener);
                        resetBtns();
                    }
                };

                chrome.downloads.onChanged.addListener(listener);
            });
        } catch (error) {
            console.error(error);
            setStatus('Connection error. Is server up?', 'error');
            resetBtns();
        }
    }

    function resetBtns() {
        downloadBtn.disabled = false;
        downloadMp4Btn.disabled = false;

        [downloadBtn, downloadMp4Btn].forEach((btn) => {
            const btnText = btn.querySelector('.btn-text');
            const spinner = btn.querySelector('.spinner');
            if (btnText) {
                btnText.style.display = 'block';
            }
            if (spinner) {
                spinner.style.display = 'none';
            }
        });
    }

    settingsBtn.addEventListener('click', () => {
        chrome.runtime.openOptionsPage();
    });

    downloadBtn.addEventListener('click', () => handleDownload('mp3', downloadBtn));
    downloadMp4Btn.addEventListener('click', () => handleDownload('mp4', downloadMp4Btn));
});
