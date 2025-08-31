chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'saveScreenshot') {
    chrome.tabs.captureVisibleTab(null, { format: 'png' }, (dataUrl) => {
      const link = document.createElement('a');
      link.href = dataUrl;
      link.download = `error_screenshot_${new Date().toISOString()}.png`;
      link.click();
    });
  }
});