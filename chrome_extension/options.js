document.addEventListener('DOMContentLoaded', () => {
    const youtubeServerInput = document.getElementById('youtube-server-url');
    const socialServerInput = document.getElementById('social-server-url');
    const saveBtn = document.getElementById('save-btn');
    const statusMessage = document.getElementById('status-message');

    chrome.storage.sync.get(['serverUrl', 'youtubeServerUrl', 'socialServerUrl'], (result) => {
        const legacyUrl = result.serverUrl || '';
        youtubeServerInput.value = result.youtubeServerUrl || '';
        socialServerInput.value = result.socialServerUrl || legacyUrl;
    });

    saveBtn.addEventListener('click', () => {
        const youtubeServerUrl = youtubeServerInput.value.trim().replace(/\/$/, '');
        const socialServerUrl = socialServerInput.value.trim().replace(/\/$/, '');

        chrome.storage.sync.set({ youtubeServerUrl, socialServerUrl }, () => {
            statusMessage.textContent = 'Settings saved successfully!';
            statusMessage.className = 'status-message success';
            setTimeout(() => {
                statusMessage.textContent = '';
                statusMessage.className = 'status-message';
                window.close();
            }, 1500);
        });
    });
});
