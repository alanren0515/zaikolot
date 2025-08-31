(function () {
  console.log('内容脚本已运行');

  // 辅助函数：等待元素出现（支持 CSS 选择器）
  function waitForElement(selector, timeout = 15000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const interval = setInterval(() => {
        const element = document.querySelector(selector);
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

  // 辅助函数：等待 XPath 选择器
  function waitForXPath(xpath, timeout = 15000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      const interval = setInterval(() => {
        const result = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null);
        const element = result.singleNodeValue;
        if (element) {
          clearInterval(interval);
          resolve(element);
        } else if (Date.now() - startTime > timeout) {
          clearInterval(interval);
          reject(new Error(`Timeout waiting for XPath: ${xpath}`));
        }
      }, 500);
    });
  }

  // 辅助函数：随机延迟
  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // 辅助函数：勾选 checkbox
  async function checkCheckbox(id) {
    try {
      const checkbox = await waitForElement(`#${id}`);
      if (!checkbox.checked) {
        await sleep(500); // 模拟原始脚本的 time.sleep(0.5)
        checkbox.click();
        console.log(`已勾选: ${id}`);
      } else {
        console.log(`已经勾选: ${id}`);
      }
    } catch (error) {
      console.error(`勾选 ${id} 时出错: ${error.message}`);
    }
  }

  // 主自动化逻辑
  async function automate() {
    try {
      // 1. 等待页面加载完成
      console.log('等待页面加载...');
      await waitForElement('body', 15000); // 确保页面加载
      console.log('页面加载完成');

      // 2. 勾选特定的 checkbox
      console.log('开始勾选 checkbox...');
      const checkboxIds = ['pay-later', 'checkboxZaikoTos', 'checkboxProfileTos'];
      for (const id of checkboxIds) {
        await checkCheckbox(id);
      }

      // 3. 点击提交按钮
      console.log('寻找并点击提交按钮...');
      const submitButton = await waitForElement('button.btn.btn-block.btn-xl.btn-brand', 15000);
      await sleep(500);
      submitButton.click();
      console.log('成功点击提交按钮：抽選を申し込む');

      // 4. 处理确认弹窗
      console.log('等待确认弹出窗口出现...');
      await waitForElement('#lottery-confirmation-modal___BV_modal_body_', 15000);
      console.log('确认弹出窗口已显示');
      const confirmButton = await waitForElement('button.btn.btn-block.primary-button.py-4.btn-pink', 15000);
      await sleep(500);
      confirmButton.click();
      console.log('已点击确认弹出窗口中的“申し込む”按钮');

      // 5. 处理成功弹窗
      console.log('等待成功弹出窗口出现...');
      try {
        await waitForElement('#lottery-success-modal___BV_modal_body_', 15000);
        console.log('成功弹出窗口已显示');
        const successButton = await waitForXPath('//a[contains(text(), "抽選状況を確認する")]', 10000);
        await sleep(500);
        successButton.click();
        console.log('已点击成功弹出窗口中的“抽選状況を確認する”按钮');
      } catch (error) {
        console.error(`主选择器失败: ${error.message}`);
        console.log('尝试备用选择器...');
        const fallbackButton = await waitForElement('a.btn.btn-block.primary-button.py-4.btn-pink', 10000);
        await sleep(500);
        fallbackButton.click();
        console.log('使用备用选择器成功点击按钮');
      }

      console.log('流程执行完成！');
    } catch (error) {
      console.error(`自动化过程中出错: ${error.message}`);
      chrome.runtime.sendMessage({ action: 'saveScreenshot' });
    }
  }

  // 自动运行（无需等待消息）
  setTimeout(automate, 1000); // 延迟 1 秒以确保页面动态内容加载
})();