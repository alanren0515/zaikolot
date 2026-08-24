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

function updateIcon(enabled) {
  chrome.action.setIcon({
    path: enabled ? ICONS.on : ICONS.off
  });
}

function syncIcon() {
  chrome.storage.local.get({ enabled: false }, ({ enabled }) => {
    updateIcon(enabled);
  });
}

function configureSidePanel() {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
    .catch((error) => console.error('[Zaiko Lottery Helper] Side Panel setup failed:', error));
}

chrome.runtime.onInstalled.addListener(() => {
  configureSidePanel();
  syncIcon();
});

chrome.runtime.onStartup.addListener(() => {
  configureSidePanel();
  syncIcon();
});

configureSidePanel();

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== 'local' || !changes.enabled) {
    return;
  }

  updateIcon(Boolean(changes.enabled.newValue));
});
