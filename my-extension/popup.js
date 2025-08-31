document.getElementById('startButton').addEventListener('click', () => {
  const urlInput = document.getElementById('urlInput').value;
  const statusDiv = document.getElementById('status');

  // 验证 URL
  if (!urlInput.startsWith('https://akb48.zaiko.io/') && !urlInput.startsWith('https://zaiko.io/')) {
    statusDiv.textContent = '请输入有效的 akb48.zaiko.io URL';
    return;
  }

  // 打开新标签页
  chrome.tabs.create({ url: urlInput }, (tab) => {
    chrome.tabs.onUpdated.addListener(function listener(tabId, changeInfo) {
      if (tabId === tab.id && changeInfo.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ['content.js']
        }, (results) => {
          if (chrome.runtime.lastError) {
            statusDiv.textContent = `脚本注入失败: ${chrome.runtime.lastError.message}`;
          } else {
            statusDiv.textContent = '自动化脚本已注入！';
          }
        });
      }
    });
  });
});