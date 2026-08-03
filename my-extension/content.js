(function () {
  if (window.__zaikoLotteryHelperInstalled) {
    return;
  }

  window.__zaikoLotteryHelperInstalled = true;

  const LOG_PREFIX = '[Zaiko Lottery Helper]';
  const CHECKBOX_IDS = ['pay-later', 'checkboxZaikoTos', 'checkboxProfileTos'];
  const SUBMIT_SELECTOR = 'button.btn.btn-block.btn-xl.btn-brand';
  const PAGE_READY_TIMEOUT = 60000;
  const ELEMENT_TIMEOUT = 30000;
  const CHECKBOX_CONFIRM_TIMEOUT = 5000;
  const MAX_BACKGROUND_WAIT = 300000;
  const POLL_INTERVAL = 500;

  let isEnabled = false;
  let activeRun = null;

  function log(message) {
    console.log(`${LOG_PREFIX} ${message}`);
  }

  function createAbortError(message = '脚本已关闭，停止自动执行') {
    const error = new Error(message);
    error.name = 'AbortError';
    return error;
  }

  function ensureEnabled(signal) {
    if (!isEnabled || signal.aborted) {
      throw createAbortError();
    }
  }

  function waitForCondition(check, description, timeout, signal) {
    return new Promise((resolve, reject) => {
      let settled = false;
      let intervalId;
      let observer;
      let visibleStartedAt = document.visibilityState === 'visible' ? Date.now() : null;
      const hardDeadline = Date.now() + Math.max(timeout, MAX_BACKGROUND_WAIT);

      function cleanup() {
        clearInterval(intervalId);
        observer?.disconnect();
        document.removeEventListener('visibilitychange', handleVisibilityChange);
        signal.removeEventListener('abort', handleAbort);
      }

      function finish(callback, value) {
        if (settled) {
          return;
        }

        settled = true;
        cleanup();
        callback(value);
      }

      function handleAbort() {
        finish(reject, createAbortError());
      }

      function handleVisibilityChange() {
        visibleStartedAt = document.visibilityState === 'visible' ? Date.now() : null;
        checkNow();
      }

      function checkNow() {
        if (settled) {
          return;
        }

        if (!isEnabled || signal.aborted) {
          finish(reject, createAbortError());
          return;
        }

        if (Date.now() >= hardDeadline) {
          finish(reject, new Error(`Timeout waiting for ${description}`));
          return;
        }

        if (document.visibilityState === 'visible' && visibleStartedAt === null) {
          visibleStartedAt = Date.now();
        }

        if (visibleStartedAt !== null && Date.now() - visibleStartedAt >= timeout) {
          finish(reject, new Error(`Timeout waiting for ${description}`));
          return;
        }

        const result = check();
        if (result) {
          finish(resolve, result);
        }
      }

      signal.addEventListener('abort', handleAbort, { once: true });
      document.addEventListener('visibilitychange', handleVisibilityChange);

      if (document.documentElement) {
        observer = new MutationObserver(checkNow);
        observer.observe(document.documentElement, {
          childList: true,
          subtree: true,
          attributes: true,
          attributeFilter: ['class', 'style', 'hidden', 'disabled', 'aria-hidden']
        });
      }

      intervalId = setInterval(checkNow, POLL_INTERVAL);
      checkNow();
    });
  }

  function waitForElement(selector, signal, timeout = ELEMENT_TIMEOUT) {
    return waitForCondition(
      () => findVisibleElement(selector),
      `element: ${selector}`,
      timeout,
      signal
    );
  }

  function waitForElementById(id, signal, timeout = ELEMENT_TIMEOUT) {
    return waitForCondition(
      () => document.getElementById(id),
      `element id: ${id}`,
      timeout,
      signal
    );
  }

  function waitForTextLink(text, signal, timeout = ELEMENT_TIMEOUT) {
    return waitForCondition(
      () => Array.from(document.querySelectorAll('a')).find((element) => {
        return isVisible(element) && element.textContent.includes(text);
      }),
      `link text: ${text}`,
      timeout,
      signal
    );
  }

  function waitForLotteryPage(signal) {
    return waitForCondition(
      () => {
        const hasKnownCheckbox = CHECKBOX_IDS.some((id) => document.getElementById(id));
        const hasSubmitButton = Boolean(findVisibleElement(SUBMIT_SELECTOR));
        return hasKnownCheckbox || hasSubmitButton;
      },
      'lottery page elements',
      PAGE_READY_TIMEOUT,
      signal
    );
  }

  function findVisibleElement(selector) {
    return Array.from(document.querySelectorAll(selector)).find(isVisible);
  }

  function findCheckboxClickTarget(checkbox) {
    const linkedLabel = Array.from(document.querySelectorAll('label')).find((label) => {
      return label.htmlFor === checkbox.id && isVisible(label);
    });

    if (linkedLabel) {
      return linkedLabel;
    }

    const parentLabel = checkbox.closest('label');
    if (parentLabel && isVisible(parentLabel)) {
      return parentLabel;
    }

    const roleCheckbox = checkbox.closest('[role="checkbox"]');
    if (roleCheckbox && isVisible(roleCheckbox)) {
      return roleCheckbox;
    }

    return checkbox;
  }

  function isCheckboxSelected(checkbox) {
    if (checkbox.checked || checkbox.getAttribute('aria-checked') === 'true') {
      return true;
    }

    const stateContainer = checkbox.closest('[role="checkbox"]');
    return Boolean(stateContainer && stateContainer.getAttribute('aria-checked') === 'true');
  }

  function isVisible(element) {
    const rect = element.getBoundingClientRect();
    const style = window.getComputedStyle(element);

    return rect.width > 0 &&
      rect.height > 0 &&
      style.visibility !== 'hidden' &&
      style.display !== 'none';
  }

  function sleep(ms, signal) {
    return new Promise((resolve, reject) => {
      let timerId = setTimeout(() => {
        signal.removeEventListener('abort', handleAbort);
        resolve();
      }, ms);

      function handleAbort() {
        clearTimeout(timerId);
        timerId = null;
        reject(createAbortError());
      }

      if (signal.aborted) {
        handleAbort();
        return;
      }

      signal.addEventListener('abort', handleAbort, { once: true });
    });
  }

  async function checkCheckbox(id, signal) {
    ensureEnabled(signal);
    const checkbox = await waitForElementById(id, signal);
    ensureEnabled(signal);

    if (isCheckboxSelected(checkbox)) {
      log(`已经勾选: ${id}`);
      return;
    }

    for (let attempt = 1; attempt <= 2; attempt += 1) {
      await sleep(500, signal);
      ensureEnabled(signal);

      const currentCheckbox = document.getElementById(id) || checkbox;
      const clickTarget = findCheckboxClickTarget(currentCheckbox);
      clickTarget.click();

      try {
        await waitForCondition(
          () => {
            const updatedCheckbox = document.getElementById(id);
            return updatedCheckbox && isCheckboxSelected(updatedCheckbox) ? updatedCheckbox : null;
          },
          `checkbox selected: ${id}`,
          CHECKBOX_CONFIRM_TIMEOUT,
          signal
        );
        log(`已确认勾选: ${id}`);
        return;
      } catch (error) {
        if (error.name === 'AbortError') {
          throw error;
        }

        if (attempt === 2) {
          throw new Error(`无法确认 checkbox 已勾选: ${id}`);
        }

        log(`第一次点击未确认成功，重试: ${id}`);
      }
    }
  }

  async function automate(signal) {
    ensureEnabled(signal);

    log('等待抽选页面元素');
    await waitForLotteryPage(signal);
    ensureEnabled(signal);

    for (const id of CHECKBOX_IDS) {
      await checkCheckbox(id, signal);
    }

    log('点击申请按钮');
    const submitButton = await waitForElement(SUBMIT_SELECTOR, signal);
    await sleep(500, signal);
    ensureEnabled(signal);
    submitButton.click();

    log('等待确认弹窗');
    await waitForElement('#lottery-confirmation-modal___BV_modal_body_', signal);
    const confirmButton = await waitForElement(
      'button.btn.btn-block.primary-button.py-4.btn-pink',
      signal
    );
    await sleep(500, signal);
    ensureEnabled(signal);
    confirmButton.click();

    log('等待成功弹窗');
    await waitForElement('#lottery-success-modal___BV_modal_body_', signal);
    const successButton = await waitForTextLink('抽選状況を確認する', signal, 10000);
    await sleep(500, signal);
    ensureEnabled(signal);
    successButton.click();

    log('流程执行完成');
  }

  function stopAutomation() {
    if (activeRun) {
      activeRun.controller.abort();
      activeRun = null;
    }

    window.__zaikoLotteryHelperRunning = false;
  }

  function startAutomation() {
    if (!isEnabled || activeRun) {
      return;
    }

    const controller = new AbortController();
    const run = { controller };
    activeRun = run;
    window.__zaikoLotteryHelperRunning = true;

    automate(controller.signal)
      .catch((error) => {
        if (error.name === 'AbortError') {
          log('自动执行已停止');
          return;
        }

        console.error(`${LOG_PREFIX} 自动化过程中出错: ${error.message}`);
      })
      .finally(() => {
        if (activeRun === run) {
          activeRun = null;
          window.__zaikoLotteryHelperRunning = false;
        }
      });
  }

  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName !== 'local' || !changes.enabled) {
      return;
    }

    isEnabled = Boolean(changes.enabled.newValue);

    if (isEnabled) {
      log('脚本已开启，开始等待抽选页面');
      startAutomation();
      return;
    }

    log('脚本已关闭，停止后续动作');
    stopAutomation();
  });

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && isEnabled && !activeRun) {
      startAutomation();
    }
  });

  window.addEventListener('pageshow', () => {
    if (isEnabled && !activeRun) {
      startAutomation();
    }
  });

  chrome.storage.local.get({ enabled: false }, ({ enabled }) => {
    isEnabled = Boolean(enabled);

    if (!isEnabled) {
      log('脚本当前为关闭状态');
      return;
    }

    startAutomation();
  });
})();
