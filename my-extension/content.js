(function () {
  if (window.__zaikoLotteryHelperInstalled) {
    return;
  }

  window.__zaikoLotteryHelperInstalled = true;

  const LOG_PREFIX = '[Zaiko Lottery Helper]';
  const OTHER_PAYMENT_TEXT = '当選後他の方法で支払う';
  const REQUIRED_TERMS_IDS = ['checkboxZaikoTos', 'checkboxProfileTos'];
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

  function waitForSuccessButton(signal, timeout = ELEMENT_TIMEOUT) {
    return waitForCondition(
      () => {
        const statusLink = findVisibleElement('a[href*="/lottery/status"]');
        if (statusLink) {
          return statusLink;
        }

        return Array.from(document.querySelectorAll('a, button')).find((element) => {
          return isVisible(element) && containsText(element, '抽選状況を確認する');
        });
      },
      'lottery status action',
      timeout,
      signal
    );
  }

  function waitForLotteryPage(signal) {
    return waitForCondition(
      () => {
        const hasOtherPaymentOption = Boolean(findOtherPaymentControl());
        const hasSubmitButton = Boolean(findVisibleElement(SUBMIT_SELECTOR));
        return hasOtherPaymentOption || hasSubmitButton;
      },
      'lottery page elements',
      PAGE_READY_TIMEOUT,
      signal
    );
  }

  function findVisibleElement(selector) {
    return Array.from(document.querySelectorAll(selector)).find(isVisible);
  }

  function normalizeText(text) {
    return text.replace(/\s+/g, ' ').trim();
  }

  function containsText(element, text) {
    return normalizeText(element.textContent).includes(normalizeText(text));
  }

  function findOtherPaymentControl() {
    const labels = Array.from(document.querySelectorAll('label')).filter((label) => {
      return isVisible(label) && containsText(label, OTHER_PAYMENT_TEXT);
    });

    for (const label of labels) {
      if (label.control) {
        return label.control;
      }

      const input = label.querySelector('input[type="checkbox"], input[type="radio"]');
      if (input) {
        return input;
      }
    }

    const roleControls = Array.from(document.querySelectorAll('[role="checkbox"], [role="radio"]'))
      .filter((element) => isVisible(element) && containsText(element, OTHER_PAYMENT_TEXT));

    for (const roleControl of roleControls) {
      return roleControl.querySelector('input[type="checkbox"], input[type="radio"]') || roleControl;
    }

    const textCandidates = Array.from(document.querySelectorAll('span, div, p'))
      .filter((element) => isVisible(element) && containsText(element, OTHER_PAYMENT_TEXT))
      .sort((left, right) => left.textContent.length - right.textContent.length);

    for (const textCandidate of textCandidates) {
      let container = textCandidate;
      for (let depth = 0; container && depth < 5; depth += 1) {
        const control = container.querySelector(
          'input[type="checkbox"], input[type="radio"], [role="checkbox"], [role="radio"]'
        );
        if (control) {
          return control;
        }
        container = container.parentElement;
      }
    }

    return null;
  }

  function isCheckboxSelected(control) {
    if (control.checked || control.getAttribute('aria-checked') === 'true') {
      return true;
    }

    const stateContainer = control.closest('[role="checkbox"], [role="radio"]');
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

  async function selectCheckbox(getControl, description, signal) {
    ensureEnabled(signal);
    const checkbox = await waitForCondition(
      getControl,
      description,
      ELEMENT_TIMEOUT,
      signal
    );
    ensureEnabled(signal);

    if (isCheckboxSelected(checkbox)) {
      log(`已经勾选: ${description}`);
      return;
    }

    for (let attempt = 1; attempt <= 2; attempt += 1) {
      await sleep(500, signal);
      ensureEnabled(signal);

      const currentCheckbox = getControl() || checkbox;
      currentCheckbox.click();

      try {
        await waitForCondition(
          () => {
            const updatedCheckbox = getControl();
            return updatedCheckbox && isCheckboxSelected(updatedCheckbox) ? updatedCheckbox : null;
          },
          `checkbox selected: ${description}`,
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
          throw new Error(`无法确认 checkbox 已勾选: ${description}`);
        }

        log(`第一次点击未确认成功，重试: ${description}`);
      }
    }
  }

  async function checkCheckboxById(id, signal) {
    return selectCheckbox(
      () => document.getElementById(id),
      `checkbox id: ${id}`,
      signal
    );
  }

  async function checkOtherPaymentOption(signal) {
    return selectCheckbox(
      findOtherPaymentControl,
      `支付方式: ${OTHER_PAYMENT_TEXT}`,
      signal
    );
  }

  async function automate(signal) {
    ensureEnabled(signal);

    log('等待抽选页面元素');
    await waitForLotteryPage(signal);
    ensureEnabled(signal);

    await checkOtherPaymentOption(signal);

    for (const id of REQUIRED_TERMS_IDS) {
      await checkCheckboxById(id, signal);
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

    log('等待申请成功状态');
    const successButton = await waitForSuccessButton(signal);
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
