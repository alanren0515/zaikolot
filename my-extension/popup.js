const enabledToggle = document.getElementById('enabledToggle');
const statusText = document.getElementById('status');

const ICONS = {
  on: {
    16: 'icons/icon-on-16.png',
    32: 'icons/icon-on-32.png',
    48: 'icons/icon-on-48.png',
    128: 'icons/icon-on-128.png'
  },
  off: {
    16: 'icons/icon-off-16.png',
    32: 'icons/icon-off-32.png',
    48: 'icons/icon-off-48.png',
    128: 'icons/icon-off-128.png'
  }
};

function updateStatus(enabled) {
  statusText.textContent = enabled ? '已开启' : '已关闭';
  statusText.classList.toggle('active', enabled);
  statusText.classList.toggle('inactive', !enabled);
}

function updateIcon(enabled) {
  chrome.action.setIcon({
    path: enabled ? ICONS.on : ICONS.off
  });
}

chrome.storage.local.get({ enabled: false }, ({ enabled }) => {
  enabledToggle.checked = enabled;
  updateStatus(enabled);
  updateIcon(enabled);
});

enabledToggle.addEventListener('change', () => {
  const enabled = enabledToggle.checked;

  chrome.storage.local.set({ enabled }, () => {
    updateStatus(enabled);
    updateIcon(enabled);
  });
});
