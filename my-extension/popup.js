import { parseUrlList } from './url-list.mjs';
import { openUrlQueue } from './url-queue.mjs';

const OPEN_INTERVAL_MS = 5000;

const enabledToggle = document.getElementById('enabledToggle');
const statusText = document.getElementById('status');
const urlInput = document.getElementById('urlInput');
const startButton = document.getElementById('startButton');
const queueStatus = document.getElementById('queueStatus');

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

function setQueueStatus(message, state = '') {
  queueStatus.textContent = message;
  queueStatus.classList.toggle('error', state === 'error');
  queueStatus.classList.toggle('success', state === 'success');
}

function sleep(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

chrome.storage.local.get({ enabled: false, urlQueueText: '' }, ({ enabled, urlQueueText }) => {
  enabledToggle.checked = enabled;
  urlInput.value = urlQueueText;
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

urlInput.addEventListener('change', () => {
  chrome.storage.local.set({ urlQueueText: urlInput.value });
});

startButton.addEventListener('click', async () => {
  const result = parseUrlList(urlInput.value);

  if (result.invalidLines.length > 0) {
    const lineNumbers = result.invalidLines.map(({ lineNumber }) => lineNumber).join('、');
    setQueueStatus(`第 ${lineNumbers} 行不是有效的 HTTP(S) URL，请修正后重试。`, 'error');
    return;
  }

  if (result.urls.length === 0) {
    setQueueStatus('请至少输入一个 URL。', 'error');
    return;
  }

  startButton.disabled = true;
  urlInput.disabled = true;

  try {
    await chrome.storage.local.set({ urlQueueText: urlInput.value });
    await openUrlQueue(result.urls, {
      intervalMs: OPEN_INTERVAL_MS,
      openTab: (createProperties) => chrome.tabs.create(createProperties),
      wait: sleep,
      onProgress: (opened, total) => setQueueStatus(`已打开 ${opened} / ${total}`)
    });

    setQueueStatus(`完成：已在后台打开 ${result.urls.length} 个 URL。`, 'success');
  } catch (error) {
    console.error('[Zaiko Lottery Helper] Failed to open URL queue:', error);
    setQueueStatus('打开标签页时发生错误，请重试。', 'error');
  } finally {
    startButton.disabled = false;
    urlInput.disabled = false;
  }
});
