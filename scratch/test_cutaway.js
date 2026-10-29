const proc = require('child_process').spawn('C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe', [
  '--headless',
  '--remote-debugging-port=9222',
  '--disable-gpu',
  'file:///D:/NIH_roorkee/FULL%20WORK%20FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/prototype_v4.html'
]);

setTimeout(async () => {
  try {
    const res = await fetch('http://localhost:9222/json');
    const tabs = await res.json();
    const pageTab = tabs.find(t => t.type === 'page');

    const ws = new WebSocket(pageTab.webSocketDebuggerUrl);
    ws.onopen = () => {
      ws.send(JSON.stringify({ id: 1, method: 'Runtime.enable' }));
      setTimeout(() => {
        ws.send(JSON.stringify({
          id: 2,
          method: 'Runtime.evaluate',
          params: { expression: "applyCameraPreset('cutaway');" }
        }));
      }, 500);

      setTimeout(() => {
        ws.send(JSON.stringify({ id: 3, method: 'Page.captureScreenshot' }));
      }, 2000);
    };

    ws.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      if (data.id === 3 && data.result && data.result.data) {
        require('fs').writeFileSync('D:/NIH_roorkee/FULL WORK FINAL_DIGITAL_NAYA_PANI/NAYA_PAANI/scratch/prototype_v4_cutaway.png', Buffer.from(data.result.data, 'base64'));
        console.log('Cutaway screenshot saved!');
        proc.kill();
        process.exit(0);
      }
    };
  } catch (err) {
    console.error(err);
    proc.kill();
  }
}, 2500);
