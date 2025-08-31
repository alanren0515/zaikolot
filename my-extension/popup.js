document.getElementById('startButton').addEventListener('click', () => {
  const urlInput = document.getElementById('urlInput').value;
  const statusDiv = document.getElementById('status');

  // 验证 URL 是否有效
  if (!urlInput.startsWith('https://akb48.zaiko.io/')) {
    statusDiv.textContent = '请输入有效的 akb48.zaiko.io URL';
    return;
  }

  // 打开新标签页
  chrome.tabs.create({ url: urlInput }, (tab) => {
    // 等待标签页加载完成后再注入 content.js
    chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
      if (tabId === tab.id && changeInfo.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        }, () => {
          statusDiv.textContent = '自动化脚本已注入！';
        });
      }
    });
  });
});