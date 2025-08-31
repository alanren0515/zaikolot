// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', () => {
  console.log('内容脚本已运行');

  // 辅助函数：等待元素出现
  function waitForElement(selector, timeout = 10000) {
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

  // 辅助函数：勾选 checkbox
  async function checkCheckbox(id) {
    try {
      const checkbox = await waitForElement(`#${id}`);
      if (!checkbox.checked) {
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
      // 1. 勾选 checkbox
      console.log('开始勾选 checkbox...');
      const checkboxIds = ['pay-later', 'checkboxZaikoTos', 'checkboxProfileTos'];
      for (const id of checkboxIds) {
        await checkCheckbox(id);
      }

      // 2. 点击提交按钮
      console.log('寻找并点击提交按钮...');
      const submitButton = await waitForElement('button.btn.btn-block.btn-xl.btn-brand');
      submitButton.click();
      console.log('成功点击提交按钮：抽選を申し込む');

      // 3. 处理确认弹窗
      console.log('等待确认弹窗...');
      await waitForElement('#lottery-confirmation-modal___BV_modal_body_');
      console.log('确认弹窗已显示');
      const confirmButton = await waitForElement('button.btn.btn-block.primary-button.py-4.btn-pink');
      confirmButton.click();
      console.log('已点击确认弹窗中的“申し込む”按钮');

      // 4. 处理成功弹窗
      console.log('等待成功弹窗...');
      await waitForElement('#lottery-success-modal___BV_modal_body_');
      console.log('成功弹窗已显示');
      try {
        const successButton = await waitForElement('a[href*="/lottery/status"]', 5000);
        successButton.click();
        console.log('已点击成功弹窗中的“抽選状況を確認する”按钮');
      } catch (error) {
        console.error(`主选择器失败: ${error.message}`);
        console.log('尝试备用选择器...');
        const fallbackButton = await waitForElement('a.btn.btn-block.primary-button.py-4.btn-pink');
        fallbackButton.click();
        console.log('使用备用选择器成功点击按钮');
      }

      console.log('流程执行完成！');
    } catch (error) {
      console.error(`自动化过程中出错: ${error.message}`);
      // 保存错误截图（通过发送消息到 background.js）
      chrome.runtime.sendMessage({ action: 'saveScreenshot' });
    }
  }

  // 执行自动化
  automate();
});