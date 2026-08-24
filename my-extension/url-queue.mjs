export async function openUrlQueue(urls, options) {
  const {
    intervalMs,
    openTab,
    wait,
    onProgress = () => {}
  } = options;

  for (let index = 0; index < urls.length; index += 1) {
    await openTab({ url: urls[index], active: false });
    onProgress(index + 1, urls.length);

    if (index < urls.length - 1) {
      await wait(intervalMs);
    }
  }
}
