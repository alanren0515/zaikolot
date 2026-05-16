const enabledToggle = document.getElementById('enabledToggle');
const statusText = document.getElementById('status');

function updateStatus(enabled) {
  statusText.textContent = enabled ? '已开启' : '已关闭';
  statusText.classList.toggle('active', enabled);
  statusText.classList.toggle('inactive', !enabled);
}

chrome.storage.local.get({ enabled: false }, ({ enabled }) => {
  enabledToggle.checked = enabled;
  updateStatus(enabled);
});

enabledToggle.addEventListener('change', () => {
  const enabled = enabledToggle.checked;

  chrome.storage.local.set({ enabled }, () => {
    updateStatus(enabled);
  });
});
