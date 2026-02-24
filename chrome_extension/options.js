document.addEventListener('DOMContentLoaded', () => {
    const serverUrlInput = document.getElementById('server-url');
    const saveBtn = document.getElementById('save-btn');
    const statusMessage = document.getElementById('status-message');

    // Load saved settings
    chrome.storage.sync.get(['serverUrl'], (result) => {
        if (result.serverUrl) {
            serverUrlInput.value = result.serverUrl;
        }
    });

    // Save settings
    saveBtn.addEventListener('click', () => {
        const serverUrl = serverUrlInput.value.trim();

        chrome.storage.sync.set({ serverUrl }, () => {
            statusMessage.textContent = 'Settings saved successfully!';
            statusMessage.className = 'status-message success';
            setTimeout(() => {
                statusMessage.textContent = '';
                statusMessage.className = 'status-message';
                window.close(); // Close options panel
            }, 1500);
        });
    });
});
