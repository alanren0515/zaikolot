(function () {
  if (window.__zaikoLotteryHelperRunning) {
    return;
  }

  const LOG_PREFIX = '[Zaiko Lottery Helper]';
  const CHECKBOX_IDS = ['pay-later', 'checkboxZaikoTos', 'checkboxProfileTos'];
  let isEnabled = false;

  function log(message) {
    console.log(`${LOG_PREFIX} ${message}`);
  }

  function waitForElement(selector, timeout = 15000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const interval = setInterval(() => {
        if (!isEnabled) {
          clearInterval(interval);
          reject(new Error('脚本已关闭，停止等待元素'));
          return;
        }

        const element = findVisibleElement(selector);
        if (element) {
          clearInterval(interval);
          resolve(element);
        } else if (Date.now() - startTime > timeout) {
          clearInterval(interval);
          reject(new Error(`Timeout waiting for element: ${selector}`));
        }
      }, 500);
    });
  }

  function waitForElementById(id, timeout = 15000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const interval = setInterval(() => {
        if (!isEnabled) {
          clearInterval(interval);
          reject(new Error('脚本已关闭，停止等待元素'));
          return;
        }

        const element = document.getElementById(id);
        if (element) {
          clearInterval(interval);
          resolve(element);
        } else if (Date.now() - startTime > timeout) {
          clearInterval(interval);
          reject(new Error(`Timeout waiting for element id: ${id}`));
        }
      }, 500);
    });
  }

  function waitForTextLink(text, timeout = 15000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const interval = setInterval(() => {
        if (!isEnabled) {
          clearInterval(interval);
          reject(new Error('脚本已关闭，停止等待链接'));
          return;
        }

        const link = Array.from(document.querySelectorAll('a')).find((element) => {
          return isVisible(element) && element.textContent.includes(text);
        });

        if (link) {
          clearInterval(interval);
          resolve(link);
        } else if (Date.now() - startTime > timeout) {
          clearInterval(interval);
          reject(new Error(`Timeout waiting for link text: ${text}`));
        }
      }, 500);
    });
  }

  function findVisibleElement(selector) {
    return Array.from(document.querySelectorAll(selector)).find(isVisible);
  }

  function isVisible(element) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);

    return rect.width > 0 &&
      rect.height > 0 &&
      style.visibility !== 'hidden' &&
      style.display !== 'none';
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  function isLikelyLotteryPage() {
    const hasKnownCheckbox = CHECKBOX_IDS.some((id) => document.getElementById(id));
    const hasSubmitButton = Boolean(findVisibleElement('button.btn.btn-block.btn-xl.btn-brand'));

    return hasKnownCheckbox || hasSubmitButton;
  }

  function ensureEnabled() {
    if (!isEnabled) {
      throw new Error('脚本已关闭，停止自动执行');
    }
  }

  async function checkCheckbox(id) {
    ensureEnabled();
    const checkbox = await waitForElementById(id);
    ensureEnabled();

    if (!checkbox.checked) {
      await sleep(500);
      ensureEnabled();
      checkbox.click();
      log(`已勾选: ${id}`);
      return;
    }

    log(`已经勾选: ${id}`);
  }

  async function automate() {
    try {
      window.__zaikoLotteryHelperRunning = true;
      ensureEnabled();

      if (!isLikelyLotteryPage()) {
        log('当前页面不是抽选操作页面，跳过执行');
        window.__zaikoLotteryHelperRunning = false;
        return;
      }

      log('等待抽选页面加载');
      ensureEnabled();

      for (const id of CHECKBOX_IDS) {
        await checkCheckbox(id);
      }

      log('点击申请按钮');
      const submitButton = await waitForElement('button.btn.btn-block.btn-xl.btn-brand');
      await sleep(500);
      ensureEnabled();
      submitButton.click();

      log('等待确认弹窗');
      await waitForElement('#lottery-confirmation-modal___BV_modal_body_');
      const confirmButton = await waitForElement('button.btn.btn-block.primary-button.py-4.btn-pink');
      await sleep(500);
      ensureEnabled();
      confirmButton.click();

      log('等待成功弹窗');
      await waitForElement('#lottery-success-modal___BV_modal_body_');
      const successButton = await waitForTextLink('抽選状況を確認する', 10000);
      await sleep(500);
      ensureEnabled();
      successButton.click();

      log('流程执行完成');
    } catch (error) {
      console.error(`${LOG_PREFIX} 自动化过程中出错: ${error.message}`);
      window.__zaikoLotteryHelperRunning = false;
    }
  }

  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName !== 'local' || !changes.enabled) {
      return;
    }

    isEnabled = Boolean(changes.enabled.newValue);

    if (!isEnabled) {
      log('脚本已关闭，后续动作会停止');
      window.__zaikoLotteryHelperRunning = false;
    }
  });

  chrome.storage.local.get({ enabled: false }, ({ enabled }) => {
    isEnabled = Boolean(enabled);

    if (!enabled) {
      log('脚本当前为关闭状态');
      return;
    }

    setTimeout(automate, 1000);
  });
})();
